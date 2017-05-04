DPDKInfo(NB_MBUF 1048576, MBUF_SIZE 4096, MBUF_CACHE_SIZE 512, MEMPOOL_PREFIX ovs_mp_1500_0_);

//// CONFIG
define($GUARANTEED_VIDEO_BANDWIDTH 2000);  // in pkts per second

routingTable :: RadixIPLookup(
  VPN_NET 0,
  INTERNAL_NET 1);

AddressInfo(INTERNAL_NET 192.168.1.0/24, 
            VPN_NET 192.168.0.0/24,
            WEB_SERVER 192.168.1.3/24,
            EXTERNAL_GW_IP 1.2.3.1/24,
            INTERNAL_GW_IP 192.168.1.1/24,
            );

// het eerste patroon zal de hoger DSCP-waarde toewijzen, tweede patroon past DSCP-waarde "0" (BE) toe
filterOutgoing::IPClassifier(dst udp port 5060 || dst tcp port 5061, // port 5060 udp/ 5061 tcp wordt gebruikt door SIP
                             -);
// eerste patroon is verkeer dat voorrang krijgt
filterIncoming::IPClassifier(ip dscp < 24,  // DSCP-waarde 24
                             -);



//// DEVICE CONFIGURATION
outRing :: ToDPDKRing(MEM_POOL 262144, FROM_PROC dpdkr0_rx, TO_PROC dpdkr0_rx, BURST 32);
out0 :: EtherVLANEncap(0x0800, 00:25:90:64:f9:65, 00:25:90:4c:76:a3, 10) 
//  -> Print("Outgoing10") 
  -> outRing;
out1 :: EtherVLANEncap(0x0800, 00:25:90:64:f9:67, 00:25:90:64:f9:5b, 11) 
//  -> Print("Outgoing11") 
  -> outRing;
fromRing :: FromDPDKRing(MEM_POOL 262144, FROM_PROC dpdkr0_tx, TO_PROC dpdkr0_tx, BURST 32)

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
//  -> Print("ARP message") 
  -> out0;
c1[0] 
//  -> Print("ARP message") 
  -> out1;


vlan[0] 
//  -> Print("VLAN is 10") 
  -> [0]c0;
vlan[1] 
//  -> Print("VLAN is 11") 
  -> [0]c1;
vlan[2] 
//  -> Print("Disallowed vlan") 
  -> Discard;


fromRing -> [0]vlan;
 
c0[1] 
  -> Paint(1) 
  -> Strip(18)
  -> CheckIPHeader(INTERFACES VPN_NET INTERNAL_NET EXTERNAL_GW_IP)
  -> filterIncoming;

c1[1] 
  -> Paint(2) 
  -> Strip(18)
  -> CheckIPHeader(INTERFACES VPN_NET INTERNAL_NET EXTERNAL_GW_IP)
  -> filterOutgoing;


filterIncoming[1] 
//  -> IPPrint(PRIORITY) 
  -> SetIPDSCP(24) 
  -> [0]routingTable; // sip traffic: markeer met DSCP-waarde 24
filterIncoming[0] 
//  -> IPPrint(NORMAL) 
  -> [0]routingTable;

priorityScheduler :: PrioSched; // priority scheduler: pakketten die aan een lagere input van dit element arriveren worden eerst verwerkt
filterOutgoing[1] 
  -> Queue(100) 
  -> [1]priorityScheduler; // best effort traffic ==> stuur naar input 1 van de scheduler
filterOutgoing[0] 
//  -> IPPrint(INVIDEO) 
  -> videoQ::Queue(10000) 
  -> BandwidthShaper($GUARANTEED_VIDEO_BANDWIDTH) 
  -> [0]priorityScheduler;
videoQ -> [2]priorityScheduler; // geef video verkeer prioriteit, maar limiteer de maximale throughput
                                // als er meer dan de maximale throughput aan video verkeer is: stuur als lagere prioriteit naar de scheduler

priorityScheduler 
  -> Unqueue() 
  -> [0]routingTable;



routingTable[0] 
  -> DropBroadcasts 
  -> IPGWOptions(EXTERNAL_GW_IP)
  -> FixIPSrc(EXTERNAL_GW_IP)
  -> DecIPTTL
  -> [0]out1;

routingTable[1] -> DropBroadcasts
  -> IPGWOptions(INTERNAL_GW_IP) // verwerk routing informatie
  -> FixIPSrc(INTERNAL_GW_IP)
  -> DecIPTTL
  -> [0]out0;

// onbekende ethertype: drop frames
c0[2] 
  -> Discard;
c1[2] 
  -> Discard;
