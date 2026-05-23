/**
 ******************************************************************************
 * File Name          : CANTask.hpp
 * Description        : canbus manager
 ******************************************************************************
 */
#ifndef CUBE_SYSTEM_CAN_TASK_HPP_
#define CUBE_SYSTEM_CAN_TASK_HPP_

/* Includes ------------------------------------------------------------------*/
#include "Task.hpp"
#include "SystemDefines.hpp"
#include <stdint.h>
#include "CanAutoNodeDaughter.hpp"
#include "DAQLogs.hpp"
#include "CANBusTargets.hpp"

/* Enums ------------------------------------------------------------------*/
enum DAQ_TASK_COMMANDS
{
    DAQ_TASK_COMMAND_NONE = 0,
    EVENT_DAQ_INIT,
    EVENT_DAQ_TEST,
    EVENT_DAQ_LOG_DATA,
    EVENT_DAQ_CLEANUP
};

/* Macros ------------------------------------------------------------------*/

extern FDCAN_HandleTypeDef hfdcan1;
/* Class ------------------------------------------------------------------*/
class CANTask : public Task
{
public:
    static CANTask &Inst()
    {
        static CANTask inst;
        return inst;
    }

    void InitTask();


    bool CANSendToMotherboardDirect(uint16_t logID, const uint8_t* msg);
    /**
	 * Any Task can use this API to send messages through the CAN Network
	 * The Board target names and log index can be found in the CanAutoNode files in the communications repository
	 */
	bool SendCANMessageToDaughter(char* aBoardName, uint8_t aLogIndex, const uint8_t* aMsg) {
		return dau.SendMessageToDaughterByLogIndex(dau.GetIDOfBoardWithName(aBoardName), aLogIndex, aMsg);
	};

protected:
    static void RunTask(void *pvParams)
    {
        CANTask::Inst().Run(pvParams);
    } // Static Task Interface, passes control to the instance Run();

    void Run(void *pvParams); // Main run code
    void HandleCommand(Command &cm);
    bool HandleCANCommands();

private:
    // Private Functions
    CANTask();                                  // Private constructor
    CANTask(const CANTask &);            // Prevent copy-construction
    CANTask &operator=(const CANTask &); // Prevent assignment
    											             //  slot index, board type
    CanAutoNodeDaughter dau = {&hfdcan1,DAQ_Init,DAQ_LogIndexes::DAQ_COUNT,234,234,CAN_ROCKET_TARGET_DAQ};

};

#endif // CUBE_SYSTEM_DAQ_TASK_HPP_
