#!/bin/bash
#
# Copyright (c) 2015-19 University of Washington
# Copyright (c) 2015 Centre Tecnologic de Telecomunicacions de Catalunya (CTTC)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation;
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

# This program runs the lte-tcp-x2-handover experiment, and generates five
# plots from the data files.
# 
# Results and all traces are stored in a timestamped 'results' directory,
# as well as the PDFs generated.

set -e
set -o errexit

control_c()
{
  echo "exiting"
  exit $?
}

trap control_c SIGINT


#Speed=(275)
#x2Distance=500
#yDistanceForUe=1000
useRlcUm=0
handoverType="A3Rsrp"
scenarioName="0.4.1"
HystVal=(3)
TTT=(256)
trials=1


dirname=lte-tcp-x2-handover
experimentDir=`pwd`


for hystVal in "${HystVal[@]}"
do
	for ttt in "${TTT[@]}"
	do
		for (( i=1; i<=$trials; i++))
		do
			resultsDir=`pwd`/results/Scenario$scenarioName-${hystVal}-${ttt}/Scenario$scenarioName-${hystVal}-${ttt}-${i}

			# need this as otherwise waf won't find the executables
			#cd ../../../../

			# Random number generator run number
			run=${i}

			mkdir -p ${resultsDir}
			#cp ${experimentDir}/*-plot.py ${resultsDir}


			#echo $speed
			echo $hystVal
			echo $ttt
			echo $i
			set -x

			./waf --run-no-build "lte-handover.cc --scenarioName=$scenarioName --RngRun=$run --trialNum=${i-1} --useRlcUm=${useRlcUm} --handoverType=${handoverType} --hystVal=${hystVal} --timeToTrigger=${ttt}"
			
			{ set +x; } 2>/dev/null

			# Move and copy files to the results directory
			if [ -f lte-tcp-x2-handover-0-2.pcap ]; then
			  mv lte-tcp-x2-handover*.pcap ${resultsDir}
			fi
			mv lte-tcp-x2-handover.*.dat ${resultsDir}
			#mv DlMacStats.txt ${resultsDir}
			#mv UlTxPhyStats.txt ${resultsDir}
			#mv UlSinrStats.txt ${resultsDir}
			#mv UlRxPhyStats.txt ${resultsDir}
			#mv UlRlcStats.txt ${resultsDir}
			#mv UlPdcpStats.txt ${resultsDir}
			#mv UlMacStats.txt ${resultsDir}
			#mv UlInterferenceStats.txt ${resultsDir}
			#mv DlTxPhyStats.txt ${resultsDir}
			#mv DlRxPhyStats.txt ${resultsDir}
			#mv DlRsrpSinrStats.txt ${resultsDir}
			#mv DlRlcStats.txt ${resultsDir}
			#mv DlPdcpStats.txt ${resultsDir}

			# git show --name-only > ${resultsDir}/git-commit.txt

			cd ${experimentDir}
			cp $0 ${resultsDir}
		done
		python3 ./Python_Analysis_Scripts/main.py $scenarioName ${hystVal} ${ttt} ${trials}
	done
done
#cd ${resultsDir}

#echo "Creating plots"

#/usr/bin/python tcp-throughput-plot.py
#/usr/bin/python mcs-plot.py
#/usr/bin/python cqi-plot.py
#/usr/bin/python rsrp-plot.py
#/usr/bin/python rsrq-plot.py

