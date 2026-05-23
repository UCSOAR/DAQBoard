/**
 ********************************************************************************
 * @file    CANMessageHandler.cpp
 * @author  Shivam Desai
 * @date    May 2, 2026
 * @brief
 ********************************************************************************
 */

/************************************
 * INCLUDES
 ************************************/
#include "CANTask.hpp"


/************************************
 * PRIVATE MACROS AND DEFINES
 ************************************/

/************************************
 * VARIABLES
 ************************************/

/************************************
 * FUNCTION DECLARATIONS
 ************************************/

/************************************
 * FUNCTION DEFINITIONS
 ************************************/
bool CANTask::HandleCANCommands() {

	{
		DAQ_AIR_BRAKES_COMMAND cmd;
		if(dau.ReadMessageByLogIndex(_DAQ_AIR_BRAKES_COMMAND_LOGINDEX, (uint8_t*)&cmd,sizeof(cmd))) {
			SOAR_PRINT("got daq airbraks cmd airbraks from rpb%d\n",cmd.airBrakesGo);
		}
	}

	return true;
};

