/* -*-  Mode: C++; c-file-style: "gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2013 Centre Tecnologic de Telecomunicacions de Catalunya (CTTC)
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 * Adapted from lena-x2-handover-measures.cc example from Manuel Requena
 *
 * Author: Manuel Requena <manuel.requena@cttc.es>
 */

/*
 * Network topology:
 *
 *      |     + --------------------------------------------------------->
 *      |     UE
 *      |
 *      |               d                   d                   d
 *    y |     |-------------------x-------------------x-------------------
 *      |     |                 eNodeB              eNodeB
 *      |   d |
 *      |     |
 *      |     |                                             d = x2Distance
 *            o (0, 0, 0)                                   y = yDistanceForUe
 */

#include <iostream>
#include <iomanip>
#include <fstream>
#include <string>
#include <sstream> // std::stringstream
#include <utility> // std::pair
#include <vector>
#include <map>
#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/mobility-module.h"
#include "ns3/netanim-module.h"
#include "ns3/lte-module.h"
#include "ns3/spectrum-module.h"
#include "ns3/applications-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/point-to-point-layout-module.h"
#include <utils/json.hpp>

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <pwd.h>
#include <sys/types.h>
#include <math.h>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("LteTcpX2Handover");

// These variables are declared outside of main() so that they may be
// referenced in the callbacks below.  They are prefixed with "g_" to
// indicate global variable status.

std::ofstream g_ueMeasurements;
std::ofstream g_packetSinkRx;
//std::ofstream g_cqiTrace;
std::ofstream g_tcpCongStateTrace;
std::ofstream g_positionTrace;

// Report on execution progress
void
ReportProgress (Time reportingInterval)
{
  std::cout << "*** Simulation time: " << std::fixed << std::setprecision (1) << Simulator::Now ().GetSeconds () << "s" << std::endl;
  Simulator::Schedule (reportingInterval, &ReportProgress, reportingInterval);
}

// Parse context strings of the form "/NodeList/3/DeviceList/1/Mac/Assoc"
// to extract the NodeId
uint32_t
ContextToNodeId (std::string context)
{
  std::string sub = context.substr (10);  // skip "/NodeList/"
  uint32_t pos = sub.find ("/Device");
  return atoi (sub.substr (0,pos).c_str ());
}

void
NotifyUdpReceived (std::string context, Ptr<const Packet> p, const Address &addr)
{
  std::cout << Simulator::Now ().GetSeconds () << " node "
            << ContextToNodeId (context)
            << " UDP received" << std::endl;
}

void
NotifyConnectionEstablishedUe (std::string context,
                               uint64_t imsi,
                               uint16_t cellid,
                               uint16_t rnti)
{
  std::cout << Simulator::Now ().GetSeconds () << " node "
            << ContextToNodeId (context)
            << " UE IMSI " << imsi
            << ": connected to CellId " << cellid
            << " with RNTI " << rnti
            << std::endl;
}

void
NotifyHandoverStartUe (std::string context,
                       uint64_t imsi,
                       uint16_t cellid,
                       uint16_t rnti,
                       uint16_t targetCellId)
{
  std::cout << Simulator::Now ().GetSeconds () << " node "
            << ContextToNodeId (context)
            << " UE IMSI " << imsi
            << ": previously connected to CellId " << cellid
            << " with RNTI " << rnti
            << ", doing handover to CellId " << targetCellId
            << std::endl;
}

void
NotifyHandoverEndOkUe (std::string context,
                       uint64_t imsi,
                       uint16_t cellid,
                       uint16_t rnti)
{
  std::cout << Simulator::Now ().GetSeconds () << " node "
            << ContextToNodeId (context)
            << " UE IMSI " << imsi
            << ": successful handover to CellId " << cellid
            << " with RNTI " << rnti
            << std::endl;
}

void
NotifyConnectionEstablishedEnb (std::string context,
                                uint64_t imsi,
                                uint16_t cellid,
                                uint16_t rnti)
{
  std::cout << Simulator::Now ().GetSeconds () << " node "
            << ContextToNodeId (context)
            << " eNB CellId " << cellid
            << ": successful connection of UE with IMSI " << imsi
            << " RNTI " << rnti
            << std::endl;
}

void
NotifyHandoverStartEnb (std::string context,
                        uint64_t imsi,
                        uint16_t cellid,
                        uint16_t rnti,
                        uint16_t targetCellId)
{
  std::cout << Simulator::Now ().GetSeconds () << " node "
            << ContextToNodeId (context)
            << " eNB CellId " << cellid
            << ": start handover of UE with IMSI " << imsi
            << " RNTI " << rnti
            << " to CellId " << targetCellId
            << std::endl;
}

void
NotifyHandoverEndOkEnb (std::string context,
                        uint64_t imsi,
                        uint16_t cellid,
                        uint16_t rnti)
{
  std::cout << Simulator::Now ().GetSeconds () << " node "
            << ContextToNodeId (context)
            << " eNB CellId " << cellid
            << ": completed handover of UE with IMSI " << imsi
            << " RNTI " << rnti
            << std::endl;
}

void
NotifyRecvMeasurementReport (std::string context,
                             uint64_t imsi,
                             uint16_t cellId,
                             uint16_t rnti,
                             LteRrcSap::MeasurementReport report)
{
  std::cout << Simulator::Now ().GetSeconds () 
            << " UE " << imsi
            << ": sent measReport to CellId " << cellId
            << std::endl;
}


void
TracePosition (Ptr<Node> ue, Time interval)
{
  Vector v = ue->GetObject<MobilityModel> ()->GetPosition ();
  g_positionTrace << std::setw (7) << std::setprecision (3) << std::fixed << Simulator::Now ().GetSeconds () << " " 
    << v.x << " " << v.y << std::endl;
  Simulator::Schedule (interval, &TracePosition, ue, interval);
}

void
NotifyUeMeasurements (std::string context, uint16_t imsi, uint16_t cellId, double rsrpDbm, double rsrqDbm, bool servingCell, uint8_t ccId)
{
  g_ueMeasurements << std::setw (7) << std::setprecision (3) << std::fixed << Simulator::Now ().GetSeconds () << " " 
    << std::setw (3) << imsi << " "
    << std::setw (3) << cellId << " " 
    << std::setw (3) << (servingCell ? "1" : "0") << " " 
    << std::setw (8) << rsrpDbm << " " 
    << std::setw (8) << rsrqDbm << std::endl;
}

void
NotifyPacketSinkRx (std::string context, Ptr<const Packet> packet, const Address &address, const Address &reciever)
{
  g_packetSinkRx << std::setw (7) << std::setprecision (3) << std::fixed << Simulator::Now ().GetSeconds () 
    << " " << std::setw (5) << packet->GetSize () << std::setw (5) << " " << reciever << std::endl;
}

/*
void
NotifyCqiReport (std::string context, uint16_t rnti, uint8_t cqi)
{
  g_cqiTrace << std::setw (7) << std::setprecision (3) << std::fixed << Simulator::Now ().GetSeconds () << " "
    << std::setw (4) << ContextToNodeId (context) << " "
    << std::setw (4) << rnti  << " " 
    << std::setw (3) << static_cast<uint16_t> (cqi) << std::endl;
}
*/

void
CongStateTrace (const TcpSocketState::TcpCongState_t oldValue, const TcpSocketState::TcpCongState_t newValue)
{
  g_tcpCongStateTrace << std::setw (7) << std::setprecision (3) << std::fixed << Simulator::Now ().GetSeconds () << " "
    << std::setw (4) << TcpSocketState::TcpCongStateName[newValue] << std::endl;
}

void
ConnectTcpTrace (void)
{
  Config::ConnectWithoutContext ("/NodeList/*/$ns3::TcpL4Protocol/SocketList/0/CongState", MakeCallback (&CongStateTrace));
}

/**
 * Program for an automatic X2-based handover based on the RSRQ measures.
 * It instantiates two eNodeB, attaches one UE to the 'source' eNB.
 * The UE moves between both eNBs, it reports measures to the serving eNB and
 * the 'source' (serving) eNB triggers the handover of the UE towards
 * the 'target' eNB when it considers it is a better eNB.
 */
int
main (int argc, char *argv[])
{
  
  // fetching the relevant simulation parameters from the configuration file
  
  
  // Constants that can be changed by command-line arguments
  //handover values
  std::string handoverType = "A3Rsrp"; //valid values are: "A3Rsrp", "A2A4RsrqHandoverAlgorithm"
  double hystVal = 3; // standards limited to: 0-15 dB (rounded to nearest .5 dB), enforced in code (values outside of range will error, values will be rounded)
  double timeToTrigger = 256; // standards limited to: 0, 40, 64, 80, 100, 128, 160, 256, 320, 480, 512, 640, 1024, 1280 ms
  double a3Offset = 0; // standards limited to: -15 dB to 15 dB
  //RLF values
  double qOut = -5;//dB
  double qIn = -3.9;//dB
  uint32_t NumQoutEvalSf = 200;//subframes
  uint32_t NumQinEvalSf = 100;//subframes
  uint32_t T310 = 1000; //standards limited to: 0, 50, 100, 200, 500, 1000, 2000
  uint32_t N310 = 6; //standards limited to: 1, 2, 3, 4, 6, 8, 10, 20
  uint32_t N311 = 2; //standards limited to: 1, 2, 3, 4, 5, 6, 8, 10
  //scenario description files
  std::string scenarioName = "0.4.1";
  int trialNum = 0;
  double numSectors = 3;
  char * homedir = getenv("HOME");
  std::string homeDir = homedir;
  std::string configFileName = homeDir + "/Dropbox/FBC_Maveric Academic Collaboration/NS-3_related_files/Simulation_Scenarios/Scenario " + scenarioName + "/trial " + std::to_string(trialNum) + "/config.json";//"/home/collin/Downloads/Scenario" + scenarioName + "/simulation_config.txt"; // this filename needs to be changed to your own local path to it
  //Other Values
  uint16_t x2HandoverDelay = 0; //subframes
  uint16_t x2HandoverAckDelay = 0; //subframes
  double enbTxPowerDbm = 46.0;
  bool useRlcUm = false;
  bool verbose = false;
  bool pcap = false;
  
  std::string scenarioFilepath = "C/";
  
  // Command line arguments
  CommandLine cmd;
  cmd.AddValue ("handoverType", "Handover type (A2A4 or A3Rsrp)", handoverType);
  cmd.AddValue ("hystVal", "Hysteresis Value", hystVal);
  cmd.AddValue ("timeToTrigger", "time to trigger (TTT)", timeToTrigger);
  cmd.AddValue ("a3Offset","A3 Offest",a3Offset);
  cmd.AddValue ("qOut","Threshold on SINR for out-of-sync indications",qOut);
  cmd.AddValue ("qIn","Threshold on SINR for in-of-sync indications",qIn);
  cmd.AddValue ("NumQoutEvalSf","Number of Frames before out-of-sync notification sent to eNb",NumQoutEvalSf);
  cmd.AddValue ("NumQinEvalSf","Number of Frames before in-of-sync notification sent to eNb",NumQinEvalSf);
  cmd.AddValue ("T310","Timer after recieveing N310 consecutive out-of-sync indications before RLF",T310);
  cmd.AddValue ("N310","the maximum number of out-of-sync notifications",N310);
  cmd.AddValue ("N311","the maximum number of in-of-sync notifications before the UE is declared back in-sync and RLF is aborted",N311);
  cmd.AddValue ("scenarioName","the name of the scenario to run",scenarioName);
  cmd.AddValue ("trialNum","the name of the scenario to run",trialNum);
  cmd.AddValue ("configFileName","Local filepath to the scenario files",configFileName);
  cmd.AddValue ("x2HandoverDelay","Number of subframes to delay the transmission of the handover request over the X-2 interface, simulates processing/transmission delay",x2HandoverDelay);
  cmd.AddValue ("x2HandoverAckDelay","Number of subframes to delay the transmission of the handover request Ack over the X-2 interface, simulates processing/transmission delay",x2HandoverAckDelay);
  cmd.AddValue ("enbTxPowerDbm", "TX power (dBm) used by eNBs", enbTxPowerDbm);
  cmd.AddValue ("useRlcUm", "Use LTE RLC UM mode", useRlcUm);
  cmd.AddValue ("pcap", "Enable pcap tracing", pcap);
  cmd.AddValue ("verbose", "Enable verbose logging", verbose);
  cmd.Parse (argc, argv);
  
  //char * homedir = getenv("HOME");
  //std::string homeDir = homedir;
  configFileName = homeDir + "/Dropbox/FBC_Maveric Academic Collaboration/NS-3_related_files/Simulation_Scenarios/Scenario " + scenarioName + "/trial " + std::to_string(trialNum) + "/config.json";//"/home/collin/Downloads/Scenario" + scenarioName + "/simulation_config.txt"; // this filename needs to be changed to your own local path to it

  
  //std::string configFileName = homeDir + "/Dropbox/FBC_Maveric Academic Collaboration/NS-3_related_files/Simulation_Scenarios/Scenario " + scenarioName + "/simulation_config.txt";//"/home/collin/Downloads/Scenario" + scenarioName + "/simulation_config.txt"; // this filename needs to be changed to your own local path to it
  //std::map<std::string,std::vector<double>> simParameters;
  
  std::ifstream  config_file(configFileName);
  nlohmann::json simParameters = nlohmann::json::parse(config_file);
  
  /*
  std::string line;
  char ch;
  std::string name;
  std::string value;
  std::vector<double> valueVec;
  
  while (std::getline(data,line))
  {
    std::stringstream lineStream(line);
    bool nameFound = false;
    name.clear();
    value.clear();
    valueVec.clear();
    while (lineStream >> ch)
    {
      if (nameFound) // the name has been found, we now want the value
      {
        value.push_back(ch);
        if(lineStream.peek() == ' ' || lineStream.peek() == '\n' || lineStream.peek() == '\r')
        {
            lineStream.ignore();
            valueVec.push_back(std::stod(value));
            value.clear();
        }
      } else // the name hasn't been found yet
      {
        name.push_back(ch);
        if(lineStream.peek() == ':') // the colon serves as the break between the name and value
        {
            lineStream.ignore();
            lineStream.ignore(); // the colon is always followed by a space, ignore that too
            nameFound = true;
        }
      }
    }
    simParameters.insert(std::pair<std::string,std::vector<double>>(name,valueVec));
  }
  
  */
  
  
  // Constants for this simulation
  //std::cout << simParameters.at("no_UE") << std::endl;
  uint16_t numberOfUes = uint16_t(simParameters["UE"].size());
  uint16_t numberOfEnbs = uint16_t(numSectors*simParameters["BS"].size());//Each eNb has three sectors which are treated as separate eNb by NS-3
  //std::cout << * << std::endl;
  // eNb/UE have to be made first to ensure that eNbID = (0,...,numeNb-1) and UEID = (numeNb,...,numeNb+numUe-1)
  NodeContainer ueNodes;
  NodeContainer enbNodes;
  enbNodes.Create (numberOfEnbs);
  ueNodes.Create (numberOfUes);
  
  
  // Additional constants (not changeable at command line)
  LogLevel logLevel = (LogLevel)(LOG_PREFIX_ALL | LOG_LEVEL_ALL);
  std::string traceFilePrefix = "lte-tcp-x2-handover";
  Time positionTracingInterval = Seconds (5);
  Time reportingInterval = Seconds (10);
  uint64_t ftpSize = 8*pow(10,12); // 2 TB
  uint16_t port = 4000;  // port number
  
  // change some default attributes based upon command line settings
  Config::SetDefault ("ns3::LteHelper::UseIdealRrc", BooleanValue (true));
  Config::SetDefault ("ns3::LteHelper::UsePdschForCqiGeneration", BooleanValue (false));
  Config::SetDefault ("ns3::LteUePhy::Qout", DoubleValue(qOut));
  Config::SetDefault ("ns3::LteUePhy::Qin", DoubleValue(qIn));
  Config::SetDefault ("ns3::LteUePhy::NumQoutEvalSf", UintegerValue(NumQoutEvalSf));
  Config::SetDefault ("ns3::LteUePhy::NumQinEvalSf", UintegerValue(NumQinEvalSf));
  Config::SetDefault ("ns3::LteUeRrc::T310", TimeValue( MilliSeconds(T310)));
  Config::SetDefault ("ns3::LteUeRrc::N310", UintegerValue(N310));
  Config::SetDefault ("ns3::LteUeRrc::N311", UintegerValue(N311));
  //Config::SetDefault ("ns3::LteUePhy::TxPower", DoubleValue (23.0));
  
  double simTime = simParameters["simulation"]["simulation_duration_s"]; // seconds
  
  
  if (verbose)
    {
      LogComponentEnable ("EpcX2", logLevel);
      LogComponentEnable ("A2A4RsrqHandoverAlgorithm", logLevel);
      LogComponentEnable ("A3RsrpHandoverAlgorithm", logLevel);
    }
  
  if (useRlcUm == false)
    {
      Config::SetDefault ("ns3::LteEnbRrc::EpsBearerToRlcMapping", EnumValue (LteEnbRrc::RLC_AM_ALWAYS));
    }
  
  g_ueMeasurements.open ((traceFilePrefix + ".ue-measurements.dat").c_str(), std::ofstream::out);
  g_ueMeasurements << "# time   imsi   cellId   isServingCell?  RSRP(dBm)  RSRQ(dB)" << std::endl;
  g_packetSinkRx.open ((traceFilePrefix + ".tcp-receive.dat").c_str(), std::ofstream::out);
  g_packetSinkRx << "# time   bytesRx" << std::endl;
  //g_cqiTrace.open ((traceFilePrefix + ".cqi.dat").c_str(), std::ofstream::out);
  //g_cqiTrace << "# time   nodeId   rnti  cqi" << std::endl;
  g_tcpCongStateTrace.open ((traceFilePrefix + ".tcp-state.dat").c_str(), std::ofstream::out);
  g_tcpCongStateTrace << "# time   congState" << std::endl;
  g_positionTrace.open ((traceFilePrefix + ".position.dat").c_str(), std::ofstream::out);
  g_positionTrace << "# time   congState" << std::endl;
  
  
  
  
  Ptr<LteHelper> lteHelper = CreateObject<LteHelper> ();
  Ptr<PointToPointEpcHelper> epcHelper = CreateObject<PointToPointEpcHelper> ();
  lteHelper->SetEpcHelper (epcHelper);
  lteHelper->SetSchedulerType ("ns3::RrFfMacScheduler");
  
  std::vector<double> hystValue (numberOfEnbs);
  for (unsigned i=0; i<hystValue.size(); ++i) hystValue[i] = hystVal;
   
  std::vector<double> TTT (numberOfEnbs);
  for (unsigned i=0; i<TTT.size(); ++i) TTT[i] = timeToTrigger;
   
  std::vector<double> A3 (numberOfEnbs);
  for (unsigned i=0; i<A3.size(); ++i) A3[i] = a3Offset;
  
  
  lteHelper->SetHandoverAlgorithmType ("ns3::A3RsrpHandoverAlgorithm");
  lteHelper->SetHandoverAlgorithmAttribute ("Hysteresis",DoubleValue (hystVal));
  lteHelper->SetHandoverAlgorithmAttribute ("TimeToTrigger",TimeValue (MilliSeconds (timeToTrigger)));
  lteHelper->SetHandoverAlgorithmAttribute ("a3Offset",DoubleValue (a3Offset));

  
  // Install Mobility Model in eNB
  Ptr<ListPositionAllocator> enbPositionAlloc = CreateObject<ListPositionAllocator> ();
  for (uint16_t i = 0; i < numberOfEnbs/numSectors; i++)
  {
    for (int j = 0; j < numSectors; ++j) //each of the three sectors shares a location
    {
      Vector enbPosition (simParameters["BS"][i]["location"][0], simParameters["BS"][i]["location"][1], simParameters["BS"][i]["location"][2]);
      enbPositionAlloc->Add (enbPosition);
    }
  }
    
  MobilityHelper enbMobility;
  enbMobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
  enbMobility.SetPositionAllocator (enbPositionAlloc);
  enbMobility.Install (enbNodes);
  
  // Install Mobility Model in UE
  MobilityHelper ueMobility;
  ueMobility.SetMobilityModel ("ns3::ConstantVelocityMobilityModel");
  ueMobility.Install (ueNodes);
  
  for (uint16_t i = 0; i < numberOfUes; i++)
  {
    Vector uePosition (simParameters["UE"][i]["initial_position"][0], simParameters["UE"][i]["initial_position"][1], simParameters["UE"][i]["initial_position"][2]);
    ueNodes.Get (i)->GetObject<MobilityModel> ()->SetPosition (uePosition);
    Vector ueVelocity (simParameters["UE"][i]["velocity"][0], simParameters["UE"][i]["velocity"][1], simParameters["UE"][i]["velocity"][2]);
    ueNodes.Get (i)->GetObject<ConstantVelocityMobilityModel> ()->SetVelocity (ueVelocity);
  }
  
  // Install LTE Devices in eNB and UEs
  Config::SetDefault ("ns3::LteEnbPhy::TxPower", DoubleValue (enbTxPowerDbm));
  NetDeviceContainer enbLteDevs = lteHelper->InstallEnbDevice (enbNodes);
  NetDeviceContainer ueLteDevs = lteHelper->InstallUeDevice (ueNodes);
  
  // LTE Helper will, by default, install Friis loss model on UL and DL
  // Set table-based pathloss model on the downlink only
  // These steps must be done after InstallEnbDevice or InstallUeDevice above
  
  Ptr<TableLossModel> tableLossModel = CreateObject<TableLossModel> ();
  Ptr<SpectrumChannel> dlChannel = lteHelper->GetDownlinkSpectrumChannel ();
  Ptr<SpectrumChannel> ulChannel = lteHelper->GetUplinkSpectrumChannel ();
  // Configure tableLossModel here, by e.g. pointing it to a trace file
  tableLossModel->initializeTraceVals(numberOfEnbs, numberOfUes, simParameters["simulation"]["resource_blocks"], simTime*1000);
  
  for (int i = 0; i < numberOfUes; ++i)
  {
  	for (int j = 0; j < numberOfEnbs/numSectors; ++j)
  	{
	  for (int k = 0; k < numSectors; ++k)
  	  {
  		  tableLossModel->LoadTrace (homeDir + "/Dropbox/FBC_Maveric Academic Collaboration/NS-3_related_files/Simulation_Scenarios/Scenario " + scenarioName + "/trial " + std::to_string(trialNum) + "/","ULDL_TX_" + std::to_string(j+1) + "_Sector_" + std::to_string(k+1) + "_UE_" + std::to_string(i+1) + "_Channel_Response.txt");// the filepath (first input), must be changed to your local filepath for these trace files
      }
   	}
  }
  
  dlChannel->AddSpectrumPropagationLossModel (tableLossModel);
  ulChannel->AddSpectrumPropagationLossModel (tableLossModel);// we want the UL/DL channels to be reciprocal
  
  // Attach all UEs to the first eNodeB
  for (uint16_t i = 0; i < numberOfUes; i++)
    {
      lteHelper->Attach (ueLteDevs.Get (i), enbLteDevs.Get (int(simParameters["UE"][i]["initial_attachment"]) - 1));
    }
  
  // Create a single RemoteHost
  NodeContainer remoteHostContainer;
  remoteHostContainer.Create (1);
  Ptr<Node> remoteHost = remoteHostContainer.Get(0);
  InternetStackHelper internet;
  internet.Install (remoteHost);
  
  // Create the notional Internet
  PointToPointHelper p2ph;
  p2ph.SetDeviceAttribute ("DataRate", DataRateValue (DataRate ("100Gb/s")));
  p2ph.SetDeviceAttribute ("Mtu", UintegerValue (1500));
  p2ph.SetChannelAttribute ("Delay", TimeValue (Seconds (0.010)));
  NetDeviceContainer internetDevices = p2ph.Install (epcHelper->GetPgwNode (), remoteHost);
  //PointToPointStarHelper star (numberOfUes, p2ph);
  Ipv4AddressHelper ipv4h;
  ipv4h.SetBase ("1.0.0.0", "255.0.0.0");
  Ipv4InterfaceContainer internetIpIfaces = ipv4h.Assign (internetDevices);
  
  // Routing of the Internet Host (towards the LTE network)
  Ipv4StaticRoutingHelper ipv4RoutingHelper;
  Ptr<Ipv4StaticRouting> remoteHostStaticRouting = ipv4RoutingHelper.GetStaticRouting (remoteHost->GetObject<Ipv4> ());
  // interface 0 is localhost, 1 is the p2p device
  remoteHostStaticRouting->AddNetworkRouteTo (Ipv4Address ("7.0.0.0"), Ipv4Mask ("255.0.0.0"), 1);
  
  // Install the IP stack on the UEs
  internet.Install (ueNodes);
  Ipv4InterfaceContainer ueIpIfaces;
  ueIpIfaces = epcHelper->AssignUeIpv4Address (NetDeviceContainer (ueLteDevs));
  
  // Update the static routing table with the addresses of the UE
  Ptr<Ipv4StaticRouting> ueStaticRouting;// = ipv4RoutingHelper.GetStaticRouting (ueNodes.Get (0)->GetObject<Ipv4> ());
  
  for (uint32_t i = 0; i < numberOfUes; ++i)
  {
    ueStaticRouting = ipv4RoutingHelper.GetStaticRouting (ueNodes.Get (i)->GetObject<Ipv4> ());
    ueStaticRouting->SetDefaultRoute (epcHelper->GetUeDefaultGatewayAddress (), 1);
  }
  
  // Create the sender applications, 1 per UE, all originating from the remote node
  BulkSendHelper ftpServer ("ns3::TcpSocketFactory", Address ());
  ftpServer.SetAttribute ("MaxBytes", UintegerValue (ftpSize));
  
  ApplicationContainer sourceApps;
  
  for (uint32_t i = 0; i < numberOfUes; ++i)
  {
    AddressValue remoteAddress (InetSocketAddress (ueIpIfaces.GetAddress (i), port));
    ftpServer.SetAttribute ("Remote", remoteAddress);
    sourceApps.Add (ftpServer.Install(remoteHost));
  }
  
  sourceApps.Start (Seconds (1));
  sourceApps.Stop (Seconds (simTime));
  
  // Create the packet sinks, 1 per UE, each at 1 UE
  PacketSinkHelper sinkHelper ("ns3::TcpSocketFactory", Address ());
  
  ApplicationContainer sinkApps;
  
  for (uint32_t i = 0; i < numberOfUes; ++i)
  {
    AddressValue sinkLocalAddress (InetSocketAddress (ueIpIfaces.GetAddress (i), port));
    sinkHelper.SetAttribute ("Local", sinkLocalAddress);
    sinkApps.Add (sinkHelper.Install(ueNodes.Get(i)));
  }
  
  sinkApps.Start (Seconds (1));
  sinkApps.Stop (Seconds (simTime));
  
  
  Ptr<EpcTft> tft = Create<EpcTft> ();
  EpcTft::PacketFilter dlpf;
  dlpf.localPortStart = port;
  dlpf.localPortEnd = port;
  tft->Add (dlpf);
  EpsBearer bearer (EpsBearer::NGBR_VIDEO_TCP_DEFAULT);
  for (uint32_t i = 0; i < numberOfUes; ++i)
  {
    lteHelper->ActivateDedicatedEpsBearer (ueLteDevs.Get (i), bearer, tft);
  }
  
  // Add X2 interface
  lteHelper->AddX2Interface (enbNodes);
  
  // Tracing
  if (pcap)
    {
      p2ph.EnablePcapAll ("lte-tcp-x2-handover");
    }
  
  lteHelper->EnableLogComponents();
  lteHelper->EnablePhyTraces ();
  //lteHelper->EnableMacTraces ();
  //lteHelper->EnableRlcTraces ();
  //lteHelper->EnablePdcpTraces ();
  //Ptr<RadioBearerStatsCalculator> rlcStats = lteHelper->GetRlcStats ();
  //rlcStats->SetAttribute ("EpochDuration", TimeValue (Seconds (1.0)));
  //Ptr<RadioBearerStatsCalculator> pdcpStats = lteHelper->GetPdcpStats ();
  //pdcpStats->SetAttribute ("EpochDuration", TimeValue (Seconds (1.0)));
  
  // connect custom trace sinks for RRC connection establishment and handover notification
  Config::Connect ("/NodeList/*/DeviceList/*/LteEnbRrc/ConnectionEstablished",
                   MakeCallback (&NotifyConnectionEstablishedEnb));
  Config::Connect ("/NodeList/*/DeviceList/*/LteUeRrc/ConnectionEstablished",
                   MakeCallback (&NotifyConnectionEstablishedUe));
  Config::Connect ("/NodeList/*/DeviceList/*/LteEnbRrc/HandoverStart",
                   MakeCallback (&NotifyHandoverStartEnb));
  Config::Connect ("/NodeList/*/DeviceList/*/LteUeRrc/HandoverStart",
                   MakeCallback (&NotifyHandoverStartUe));
  Config::Connect ("/NodeList/*/DeviceList/*/LteEnbRrc/HandoverEndOk",
                   MakeCallback (&NotifyHandoverEndOkEnb));
  Config::Connect ("/NodeList/*/DeviceList/*/LteUeRrc/HandoverEndOk",
                   MakeCallback (&NotifyHandoverEndOkUe));
  Config::Connect ("/NodeList/*/DeviceList/*/LteEnbRrc/RecvMeasurementReport",
                   MakeCallback (&NotifyRecvMeasurementReport));
  // connect additional traces for more experiment tracing
  Config::Connect ("/NodeList/*/DeviceList/*/ComponentCarrierMapUe/*/LteUePhy/ReportUeMeasurements",
                   MakeCallback (&NotifyUeMeasurements));
  Config::Connect ("/NodeList/*/ApplicationList/*/$ns3::PacketSink/RxWithAddresses",
                   MakeCallback (&NotifyPacketSinkRx));
  //Config::Connect ("/NodeList/*/DeviceList/*/$ns3::LteEnbNetDevice/ComponentCarrierMap/*/FfMacScheduler/$ns3::RrFfMacScheduler/WidebandCqiReport",
  //                 MakeCallback (&NotifyCqiReport));
  
  // Delay trace connection until TCP socket comes into existence
  Simulator::Schedule (Seconds (1.001), &ConnectTcpTrace);
  // Initiate position tracing
  Simulator::Schedule (Seconds (0), &TracePosition, ueNodes.Get(0), positionTracingInterval);
  
  // Start to execute the program
  //Vector vUe = ueNodes.Get (0)->GetObject<MobilityModel> ()->GetPosition ();
  //Vector vEnb1 = enbNodes.Get (0)->GetObject<MobilityModel> ()->GetPosition ();
  //Vector vEnb2 = enbNodes.Get (1)->GetObject<MobilityModel> ()->GetPosition ();
  std::cout << "Simulation time: " << simTime << " sec" << std::endl;
  
  Simulator::Schedule (reportingInterval, &ReportProgress, reportingInterval);
  
  Simulator::Stop (Seconds (simTime));
  Simulator::Run ();
  
  // This method coordinates the deallocation of heap memory so that no
  // memory leaks are reported.
  Simulator::Destroy ();
  
  // Close any open file descriptors
  g_ueMeasurements.close ();
  //g_cqiTrace.close ();
  g_packetSinkRx.close ();
  g_tcpCongStateTrace.close ();
  g_positionTrace.close ();
  
  return 0;
}
