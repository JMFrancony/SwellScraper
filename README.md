# SwellScraper
It has been used on a VM running under Ubuntu 16.04.6 LTS and python 3.5.2
We used MongoDB 3.4.10

Built in a context of academic research, this device is used for Web page monitoring and chrono-scraping. The purpose of this research is to monitor the evolution of a set of web pages in a very dynamic content context. It has been used in the context of Caming studies (PACTE Laboratory - University of Grenoble Alpes).

http://www.theses.fr is used as an example for page collection and data extraction (this configuration was used to study the vocabulary and themes associated with scientific work on Twitter in France).

This repository concerns on one hand, the scheduling part of the monitoring and the recording of a page collection and on the other, the effective data extraction from collected pages. 

1. Monitoring the collection.
The code is organized around the scrapy module and its event management based on Twisted. 

The Agenda module deals with the activation (on/off) script of the scrapy/spider. The agenda is setup in the config file. Daily (HMS scripting) or Weekly (DHMS scripting) subclasses of agenda can be used. The module URLRoller defines a roulette of URLs which must be analyzed once or cyclically. A cycle can be suspended or interrupted by the time constraints of the agenda.

Collected pages are ziped and put into the pipeline for storage (CSV file or Mongodb Database).

2. Extracting data.



