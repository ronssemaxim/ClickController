/*        mp_name = xasprintf("ovs_mp_%d_%d_%u", dmp->mtu, dmp->socket_id,
                            mp_size);
RG_MP_ovs_mp_1500_0_262144
    _MEM_POOL = DPDKDevice::MEMPOOL_PREFIX + _MEM_POOL;
*/

//DPDKInfo(NB_MBUF 1048576, MBUF_SIZE 16384, MBUF_CACHE_SIZE 512, MEMPOOL_PREFIX ovs_mp_1500_0_);
DPDKInfo(NB_MBUF 1048576, MBUF_SIZE 4096, MBUF_CACHE_SIZE 512, MEMPOOL_PREFIX ovs_mp_1500_0_);

FromOVSDPDKRing(MEM_POOL 262144, RING_NAME dpdkr5_tx, BURST 32)
//	-> Print("incoming")
//	-> Discard;
	-> ToOVSDPDKRing(MEM_POOL 262144, RING_NAME dpdkr4_rx, BURST 32);

FromOVSDPDKRing(MEM_POOL 262144, RING_NAME dpdkr4_tx, BURST 32)
//	-> Print("outgoing")
//      -> Discard;
        -> ToOVSDPDKRing(MEM_POOL 262144, RING_NAME dpdkr5_rx, BURST 32);


