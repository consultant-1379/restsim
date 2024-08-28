#!/usr/bin/python
import sys


#Below is the usage of new framework for flexible rop implementation
def main(argv):
    print ("This script is deprecated by this new script /netsim_users/pms/bin/configFlexRop.sh(NSS-39787) , please check below commands and confluence to enable/ configure flex rop \n")

    print ("To enable flexible support for a nodetype for required rop period Execute the script in this way /netsim_users/pms/bin/configFlexRop.sh -l nodetype -r ropperiod -c ADD      Ex:1  /netsim_users/pms/bin/configFlexRop.sh -l MTAS -r 5 -c ADD \n")

    print ("To disable flexible support for a nodetype for required rop period Execute the script in this way /netsim_users/pms/bin/configFlexRop.sh -l nodetype -r ropperiod -c DELETE     Ex:1  /netsim_users/pms/bin/configFlexRop.sh -l MTAS -r 5 -c DELETE \n")

    print ("For further details Please refer this confluence:  https://confluence-oss.seli.wh.rnd.internal.ericsson.com/pages/viewpage.action?spaceKey=JXT&title=Flexible+ROPs+Support+In+Genstats \n")

    print ("The data which you enable or disable for flexible rop nodes will be present in this configuration file : /netsim_users/pms/etc/flex_rop_cfg\n")

    print ("For further support/ query please raise support ticket on NSS_PM\n")

if __name__ == "__main__":
    main(sys.argv[1:])




