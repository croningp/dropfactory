
#include <CommandHandler.h>
#include <CommandManager.h>
CommandManager cmdMng;

#include <AccelStepper.h>
#include <LinearAccelStepperActuator.h>
#include <CommandLinearAccelStepperActuator.h>

AccelStepper stp_X(AccelStepper::DRIVER, 54, 55);
CommandLinearAccelStepperActuator X(stp_X, 3, 38);

AccelStepper stp_Y(AccelStepper::DRIVER, 60, 61);
CommandLinearAccelStepperActuator Y(stp_Y, 14, 56);

AccelStepper stp_Z(AccelStepper::DRIVER, 26, 28);
CommandLinearAccelStepperActuator Z(stp_Z, 18, 24);

AccelStepper stp_S1(AccelStepper::DRIVER, 36, 34);
CommandLinearAccelStepperActuator S1(stp_S1, 19, 30);


#include <SHT1X.h>
#include <CommandSHT1X.h>
CommandSHT1X SHT15(16, 17); // Data, SCK

void setup()
{
  Serial.begin(115200);

  X.registerToCommandManager(cmdMng, "X");
  Y.registerToCommandManager(cmdMng, "Y");
  Z.registerToCommandManager(cmdMng, "Z");
  S1.registerToCommandManager(cmdMng, "S1");
  SHT15.registerToCommandManager(cmdMng, "SHT15");

  cmdMng.init();
}

void loop()
{
  cmdMng.update();
}
