#!/bin/bash
if [ -d "/docker-resources" ]; then
	# only execute the script once
	echo "Already prepped this host."
	exit
fi

# use a fixed token, to prevent user intervention to enter the token
token="af6ed7.b8e291bb3c5e22ab"
logLocation="/installLog.txt"
cd /tmp

# apt might have some locks on boot, which prevents other scripts from installing or updating packages using apt. 
# So keep trying to update untill it succeeds
until apt-get update | tee -a $logLocation
do
	echo "Apt-get update failed, retrying..." | tee -a $logLocation
	sleep 2
done

apt-get install -y curl | tee -a $logLocation

curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -  | tee -a $logLocation
cat <<EOF > /etc/apt/sources.list.d/kubernetes.list
deb http://apt.kubernetes.io/ kubernetes-xenial main
EOF
apt-get update | tee -a $logLocation

apt-get install -y docker.io | tee -a $logLocation
apt-get install -y kubelet kubeadm kubectl kubernetes-cni | tee -a $logLocation
apt-get install -y gcc libhugetlbfs-dev libpcap-dev git make python | tee -a $logLocation

kubeadm reset | tee -a $logLocation



KUBELET_EXTRA_ARGS=--enable-custom-metrics=true
export KUBELET_EXTRA_ARGS

# MASTER INIT if hostname contains kube1
if hostname | grep [a-z]*1; then
    echo "master!";

	kubeadm init --token $token | tee -a $logLocation
	cp /etc/kubernetes/admin.conf $HOME/
	chown $(id -u):$(id -g) $HOME/admin.conf
	export KUBECONFIG=$HOME/admin.conf
	echo "export KUBECONFIG=\$HOME/admin.conf" >> $HOME/.bashrc

	kubectl apply -f http://docs.projectcalico.org/v2.0/getting-started/kubernetes/installation/hosted/kubeadm/calico.yaml | tee -a $logLocation
	while kubectl get pod --all-namespaces | grep ContainerCreating;
	do
		echo "Waiting for container creation..." | tee -a $logLocation
		sleep 2;
	done;

	echo "master, waiting 2 minutes for slave nodes to connect" | tee -a $logLocation
	sleep 120
# SLAVE CONFIG
else
    echo "slave, waiting 2 minutes for master node to initialize" | tee -a $logLocation
	sleep 120

    # get the own hostname, remove computer name, prepend "kube1". Lookup the ip of the corresponding host, and this is used as the masterIp
	masterIp=$(nslookup "kube1."$(hostname | cut -d. -f2-) | grep Address | sed -n '2p' | awk '{print $2}');

	kubeadm join --token=$token $masterIp | tee -a $logLocation
fi;


# create click-controller user
useradd -s /bin/bash click-controller
mkdir -p /home/click-controller
chown click-controller:click-controller /home/click-controller # create & set permissions for home folder
echo "click-controller:Azerty123" | chpasswd # set passwd
echo "click-controller ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers # allow sudo without passwd


# configure hugepages
# get current ram free in GB, subtract 1GB to retain some freedom for other apps
numHugePages=$(($(free -g | sed -n '2p' | awk '{print $2}')-1))
echo "configuring $numHugePages hugepages" | tee -a $logLocation
echo "GRUB_CMDLINE_LINUX_DEFAULT=\"default_hugepagesz=1G hugepagesz=1G hugepages=$numHugePages hugepagesz=2M hugepages=512 intel_iommu=on\"" >> /etc/default/grub
update-grub
# TODO: https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/5/html/Tuning_and_Optimizing_Red_Hat_Enterprise_Linux_for_Oracle_9i_and_10g_Databases/sect-Oracle_9i_and_10g_Tuning_Guide-Large_Memory_Optimization_Big_Pages_and_Huge_Pages-Configuring_Huge_Pages_in_Red_Hat_Enterprise_Linux_4_or_5.html
sysctl vm.nr_hugepages=$((numHugePages))
echo $((numHugePages*5)) > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
echo $numHugePages > /sys/kernel/mm/hugepages/hugepages-1048576kB/nr_hugepages
# echo 100 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
echo "Creating mountpoint for hugepages" | tee -a $logLocation
mkdir -p /mnt/huge | tee -a $logLocation
mkdir -p /mnt/huge2MB | tee -a $logLocation
mount -t hugetlbfs none /mnt/huge | tee -a $logLocation
mount -t hugetlbfs none /mnt/huge2MB/ -o "pagesize=2M" | tee -a $logLocation


echo "Installing OVS-dpdk..." | tee -a $logLocation
apt-get install openvswitch-switch-dpdk
update-alternatives --set ovs-vswitchd /usr/lib/openvswitch-switch-dpdk/ovs-vswitchd-dpdk



# Install kernel modules
# https://gist.github.com/ConradIrwin/9077440
# http://dpdk.org/doc/guides/linux_gsg/build_dpdk.html
modprobe uio_pci_generic | tee -a $logLocation
# Enable vfio device for OpenVSwitch: modprobe vfio-pci | tee -a $logLocation
# Legacy driver: modprobe uio | tee -a $logLocation
#				 insmod build/kmod/igb_uio.ko | tee -a $logLocation
cd ..

for intf in `ifconfig | grep encap | grep ^e | cut -d" " -f1`; do
        if ifconfig $intf | grep "inet addr" | grep -q "192."; then
                echo "Enabling dpdk on $intf" | tee -a $logLocation
                # the next line will automatically bind all interfaces with an ip address in the 192.0.0.0/8 range to the uio_pci_generic driver
				#ifconfig $intf down | tee -a $logLocation
				#./usertools/dpdk-devbind.py --bind=uio_pci_generic $intf | tee -a $logLocation
				#ifconfig $intf up | tee -a $logLocation
        fi;
done