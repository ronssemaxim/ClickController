#!/bin/bash
# logging location
mkdir -p /usr/src/app/
touch /usr/src/app/run.log

verbose=false;
if [[ $* == *--verbose* ]]; then
        verbose=true;
fi

# check for number of parameters
if [ "$#" -lt 2 ]; then
        echo "Illegal number of parameters"
        echo "Usage: $0 <inputfile> <outputfile> [--start-click]"
        exit -1;
fi

function getTestContainerIp() {
	$hostname=$(hostname)
	$contName=$(ssh mrronsse@172.17.0.1 docker ps | grep click | grep -v $hostname | tail -n1 | cut -d' ' -f1)
	$tmp=$(ssh mrronsse@172.17.0.1 docker inspect $contName | grep "IPAddress" | tail -n1 | cut -d':' -f2)
	echo ${tmp:2:-2}
}



$verbose && echo "Interfaces list: " 2>&1 | tee -a /usr/src/app/run.log | tee >(logger)
$verbose && ifconfig 2>&1 | tee -a /usr/src/app/run.log | tee >(logger)

$verbose && echo "Route list:" 2>&1 | tee -a /usr/src/app/run.log | tee >(logger)
$verbose && route -n 2>&1 | tee -a /usr/src/app/run.log | tee >(logger)

if [[ $* == *--scan-interfaces* ]]; then
# process ifconfig output
i=0;
curIsDocker=false;
while read -r line
do
        # first line contains the device name and the MAC address
        if [[ $line == *"Ethernet"* ]]; then
                intfName=$(echo $line | cut -f1 -d' ');
                mac=$(echo $line | cut -f5 -d' ');
                declare "INTF_NAME_$i=$intfName"
                declare "INTF_MAC_$i=$mac"
                $verbose && echo "Found interface at pos $i: INTF_NAME_$i, with name = $intfName and mac = $mac" 2>&1 | tee -a /usr/src/app/run.log | tee >(logger)

                # determine host's IP & MAC
                if [[ $line == *"docker"* ]]; then
                        curIsDocker=true;
                fi


        fi
        # get IPv4 address
        if [[ $line == *"inet "* ]]; then
                ip=$(echo $line | cut -f2 -d' ' | cut -f2 -d:)
                declare "INTF_IP_$i=$ip"
                declare "INTF_MASK_$i=$(echo $line | cut -f4 -d' ' | cut -f2 -d:)"

                $verbose && echo "IP of intf $i: $ip" 2>&1 | tee -a /usr/src/app/run.log | tee >(logger)

                # get host ip & mac address
                # host ip: lookup default gateway, get second field
                hostIp=$(route -n | grep "^0.0.0.0" | sed 's/\s\s*/ /g' | cut -d' ' -f2);
                # ping the host once to fill the arp table
                ping -c 1 -s 1 $hostIp > /dev/null
                hostMac=$(arp -a $hostIp | cut -d' ' -f4);
                $verbose && echo "Host ip at position $i has IP $hostIp and MAC address $hostMac" 2>&1 | tee -a /usr/src/app/run.log | tee >(logger)
                declare "HOST_IP_$i=$hostIp";
                declare "HOST_MAC_$i=$hostMac";
        fi
        # get IPv6 address
        if [[ $line == *"inet6 "* ]]; then
                declare "INTF_IP6_$i=$(echo $line | cut -f3 -d' ' | cut -f1 -d/)"
                declare "INTF_MASK6_$i=$(echo $line | cut -f3 -d' ' | cut -f2 -d/)"
        fi

        # increment $i at each empty line
        if [[ -z "${line// }" ]]; then
                i=$((i+1));
        fi;
done < <(ifconfig)
fi

# loop over all the variables in this shell (including ID etc)
for var in $(compgen -v)
do
        # if the contents of the variable contain only alphanumerical characters and a "." or ":", then find & replace it
        if [[ "${!var}" =~ ^([a-z]|[A-Z]|[0-9]|:|\.)+$  &&  "$var" != "BASH_COMMAND" ]]; then
                # build up sed expression and its corresponding value
                exp=$(sed -e 's/\${/\\&}/g' <<< "$var")
                var=$(sed -e 's/\${\([^}]\+\)}/\1/' <<< "$var")
                # add to the arguments list
                $verbose && echo "Adding to seds argument list: -e s/\${$exp}/${!var}/g" 2>&1 | tee -a /usr/src/app/run.log | tee >(logger)
                args+=("-e s/\${$exp}/${!var}/g")
        fi
done

# find & replace once, reducing disk usage
sed "${args[@]}" $1 > $2

$verbose && echo "Exported variable list:" 2>&1 | tee -a /usr/src/app/run.log | tee >(logger)
$verbose && declare 2>&1 | tee -a /usr/src/app/run.log | tee >(logger)

$verbose && echo "Done!" 2>&1 | tee -a /usr/src/app/run.log | tee >(logger)


if [[ $* == *--print* ]]; then
        $verbose && echo "Resulting click file:" 2>&1 | tee -a /usr/src/app/run.log | tee >(logger)
        cat $2 2>&1 | tee -a /usr/src/app/run.log | tee >(logger)
fi


if [[ $* == *--start-click* ]]; then
        sleep 1;
#	click --dpdk -c 0x1 -n 1 --socket-mem 2048 --file-prefix test -- $2 2>&1 | tee -a /usr/src/app/run.log | tee >(logger)
        click --dpdk -l 1-23 -n 4 --lcores='(2-12)@(0,1)' --master-lcore 2 --socket-mem 1024 --no-pci --file-prefix test --proc-type=secondary -- $2 2>&1 | tee -a /usr/src/app/run.log | tee >(logger)

#        click --dpdk -l 0-3 -n 4 --lcores='(1-3)@(0,1)' --master-lcore 1 --socket-mem 1024 -b "0000:04:00.1" --file-prefix test --proc-type=primary -- $2 2>&1 | tee -a /usr/src/app/run.log | tee >(logger)
fi

exit 1;
