/*
the click.click file in the click-firewall directory will act as a firewall and prevent certain traffic from passing further down the chain.
*/
DPDKInfo(NB_MBUF 1048576, MBUF_SIZE 4096, MBUF_CACHE_SIZE 512, MEMPOOL_PREFIX ovs_mp_1500_0_);

//// CONFIG
AddressInfo(INTERNAL_NET 192.168.1.0/24, 
			VPN_NET 192.168.0.0/24,
			WEB_SERVER 192.168.1.3/24,
			EXTERNAL_GW_IP 1.2.3.1/24,
			INTERNAL_GW_IP 192.168.1.1/24);

filterIncoming::IPClassifier((dst tcp port 80 || 443) && (dst WEB_SERVER),
							 src VPN_NET && icmp type echo-reply, // accepteer Ping-replies uit het VPN-net
							 -);
filterOutgoing::IPClassifier((src tcp port 80 || 443) && (src WEB_SERVER),
							 dst VPN_NET && icmp type echo, // pingen naar het VPN-net
							 -)

routingTable :: RadixIPLookup(VPN_NET 0,
							  INTERNAL_NET 1);


//// DEVICE CONFIGURATION
outRing :: ToOVSDPDKRing(MEM_POOL 262144, RING_NAME dpdkr${dpdkr}_rx, BURST 32);
out0 :: EtherVLANEncap(0x0800, 00:25:90:64:f9:65, 00:25:90:4c:76:a3, 10) 
	//-> Print("Outgoing10") 
	-> outRing;
out1 :: EtherVLANEncap(0x0800, 00:25:90:64:f9:67, 00:25:90:64:f9:5b, 11) 
	//-> Print("Outgoing11") 
	-> outRing;
fromRing :: FromOVSDPDKRing(MEM_POOL 262144, RING_NAME dpdkr${dpdkr}_tx, BURST 32)

//// CLICK CONFIGURATION
vlan :: Classifier(14/000A,
				   14/000B,
				   -);
c0 :: Classifier(16/0806,
				 16/0800,
				 -);
 
c1 :: Classifier(16/0806,
				 16/0800,
				 -);

// arp packages ==> doorgeven in de chain, Click kan er niet op reageren doordat het niet mogelijk is om pakketten te creeren en vervolgens op een DPDK-ring te plaatsten
c0[0] 
	//-> Print("ARP message") 
	-> out0;
c1[0] 
	//-> Print("ARP message") 
	-> out1;


vlan[0] 
	//-> Print("VLAN is 10") 
	-> [0]c0;
vlan[1] 
	//-> Print("VLAN is 11") 
	-> [0]c1;
vlan[2] 
	//-> Print("Disallowed vlan") 
	-> Discard;


fromRing -> [0]vlan;
 


c0[1] 
	-> Strip(18)
	-> CheckIPHeader(INTERFACES VPN_NET INTERNAL_NET EXTERNAL_GW_IP)
	-> filterIncoming;
filterIncoming[0] -> routingTable;
filterIncoming[1] -> routingTable;
filterIncoming[2]
	//-> Print("Disallowed incoming traffic")
	-> Discard;

c1[1] 
	-> Strip(18)
	-> CheckIPHeader(INTERFACES VPN_NET INTERNAL_NET EXTERNAL_GW_IP)
	-> filterOutgoing;
filterOutgoing[0] -> routingTable;
filterOutgoing[1] -> routingTable;

filterOutgoing[2] 
	//-> Print("Disallowed outgoing traffic")
	-> Discard;
 

routingTable[0] 
	-> DropBroadcasts 
	-> IPGWOptions(EXTERNAL_GW_IP)
	-> FixIPSrc(EXTERNAL_GW_IP)
	-> DecIPTTL
	-> [0]out1;

routingTable[1] 
	-> DropBroadcasts
	-> IPGWOptions(INTERNAL_GW_IP) // verwerk routing informatie
	-> FixIPSrc(INTERNAL_GW_IP)
	-> DecIPTTL
	-> [0]out0;

// onbekende ethertype: drop frames
c0[2] -> Discard;
c1[2] -> Discard;