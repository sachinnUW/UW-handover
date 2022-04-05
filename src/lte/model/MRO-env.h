#pragma once
#include "ns3/ns3-ai-rl.h"


namespace ns3 {

struct mlInput
{
	double x;
	double y;
	double time;
	int imsi;
	int cellId;
	double packetSize;
	int packetReceiverId;
	double rsrp;
	int packetRxFlag;
        int hoInProgress;
        int hoEnded;
}Packed;

struct mlOutput
{
	double tttAdjustment;
        double hystAdjustment;
}Packed;

class MROENV : public Ns3AIRL<mlInput, mlOutput>
{
	public:
		MROENV (void) = delete;
		MROENV (uint16_t id);
		double tableRead(double x, double y);
		double tableRead2(double x, double y);
		void loadIds(double time, int imsi, int cellId, double rsrp);
                void hoStarted();
                void hoEnded();
		void passPacketReception(double time, double packetSize, int packetReceiverId);
};
}// namespace ns3

