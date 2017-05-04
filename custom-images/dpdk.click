DPDKInfo(RX_PTHRESH 0, RX_HTHRESH 0,
	RX_WTHRESH 0,
	TX_PTHRESH 0,
	TX_HTHRESH 0,
	TX_PTHRESH 0
);

FromDPDKDevice(0000:06:00.1)
//	-> Print()
	-> ToDPDKDevice(0000:08:00.1, BLOCKING false, BURST 1);
//	-> Discard;

FromDPDKDevice(0000:08:00.1) 
//	-> Print()
	-> ToDPDKDevice(0000:06:00.1, BLOCKING false, BURST 1);
//	-> Discard;

