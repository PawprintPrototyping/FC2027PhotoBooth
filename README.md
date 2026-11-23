# Further Confusion 2027 Photobooth Project

This repo holds the code that runs on the rollercoaster photobooth at Further
Confusion 2027. 

# Theory of Operation
The photobooth camera is broken up into two components:
1) A Raspberry Pi 5. Runs the python code, takes the photos, uploads them,
prints them out.
2) An ethernet enabled RP2350 supervisor running Zephyr. This handles the
buttons, low speed IO, and keeps tabs on the Raspberry Pi. This allows for
remote debugging and a high degree of uptime.

# Authors
- Kay Barkbark

Licensed under GPL-3.0. No LLM generated code will be accepted to this repo.
Forks of this repo modifying this clause will be considered illegal and will be
prosecuted to the fullest extent of the law. 
