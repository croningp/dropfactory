
#include <CommandHandler.h>
#include <CommandManager.h>
CommandManager cmdMng;

#include <AccelStepper.h>
#include <LinearAccelStepperActuator.h>
#include <CommandLinearAccelStepperActuator.h>

AccelStepper stp_G1(AccelStepper::DRIVER, 54, 55);
CommandLinearAccelStepperActuator G1(stp_G1, 3, 38);

AccelStepper stp_G2(AccelStepper::DRIVER, 60, 61);
CommandLinearAccelStepperActuator G2(stp_G2, 14, 56);

AccelStepper stp_S2(AccelStepper::DRIVER, 36, 34);
CommandLinearAccelStepperActuator S2(stp_S2, 19, 30);

AccelStepper stp_S3(AccelStepper::DRIVER, 46, 48);
CommandLinearAccelStepperActuator S3(stp_S3, 2, 62);

AccelStepper stp_S4(AccelStepper::DRIVER, 26, 28);
CommandLinearAccelStepperActuator S4(stp_S4, 18, 24);

void setup()
{
  Serial.begin(115200);

  G1.registerToCommandManager(cmdMng, "G1");
  G2.registerToCommandManager(cmdMng, "G2");
  S2.registerToCommandManager(cmdMng, "S2");
  S3.registerToCommandManager(cmdMng, "S3");
  S4.registerToCommandManager(cmdMng, "S4");


  cmdMng.init();
}

void loop()
{
  cmdMng.update();
}
