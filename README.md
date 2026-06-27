The Indyme CB440 is a customer service call button. Button is pressed, AM270 OOK signal on 303.875 MHz is sent, PA system requests personnel to button's location. Call can be canceled by pressing the other button, otherwise the PA repeats the request a few times, adding an additional chime with each repetition.

Unit is programmed by removing the JP2 jumper and holding the cancel / reset button for 5 seconds. First, hundreds are entered by pressing the main button once per hundred, just reset for numbers under 100, then tens, then reset, then ones, then reset. It will blink back the code using long and short flashes for zeros and ones. For example, to program call 302, hold reset for 5 seconds until it blinks, press the main button 3x, press reset, press reset again (for no tens), press main button twice, and press reset. It should blink short-short-short-(pause)-long-(pause)-short-short. Unit will still function normally without the JP2 jumper installed, which means that units can be negligently or intentionally deployed in a programmable state.

Idea: rather than exhaustively mapping all 999 calls (and maybe 999 cancellation calls), take a bunch of samples with Flipper Zero, as .sub files, and ideally get Claude to write a .sub generator for all 999 codes, and/or cancellations.

CB440 / CB511 technical document:
https://fcc.report/FCC-ID/J69GENCLBX/277537.pdf
