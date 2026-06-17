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
#include "LoggingService.hpp"
#include "PollingTask.hpp"
#include "CoreProto.h"


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

	// Check for rocket state messages from FCB and control logging centrally here.
	{
		uint8_t rawRocketState = 0;
		if (dau.ReadMessageByLogIndex(_DAQ_ROCKET_STATE_LOGINDEX, &rawRocketState, sizeof(rawRocketState))) {
			SOAR_PRINT("CANTask CAN | Rocket state raw byte=%u\n", (unsigned int)rawRocketState);

			// Simple mapping: 1 == FILL, 2 == TOUCHDOWN. Ignore other values.
			if (rawRocketState == 1) {
				PollingTask::Inst().SetRocketState(RocketState::RS_FILL);
				SOAR_PRINT("CANTask CAN | Mapped raw %u -> RS_FILL\n", (unsigned int)rawRocketState);
			} else if (rawRocketState == 2) {
				PollingTask::Inst().SetRocketState(RocketState::RS_TOUCHDOWN);
				SOAR_PRINT("CANTask CAN | Mapped raw %u -> RS_TOUCHDOWN\n", (unsigned int)rawRocketState);
			} else {
				// Unknown/suppressed values — do nothing to avoid unintended transitions.
			}
		}
	}

	return true;
};

