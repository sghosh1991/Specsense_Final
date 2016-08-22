Project Motivation:
===================

Mobile spectrum is at a premium thse days and with the exploding number of mobile users and video traffic on mobile phones the available spectrum
is no longer sufficient. TV white space spectrum which was meant for over the air tv broadcast is not wideley used. So we can use the less used TV White Space spectrum
(TVWS) opportunistically to offload mobile traffic. 5g technologies envisage a cognitive radio on the phone that will sense the presence of the TV spectrum
at a given location and send data using that spectrum if uit is available. For these to work we need to have a database that people can query to find the location of
available TVWS spectrum. Although mathematical models are there to precisely tell us the geographic distribution of TV spectrum (Google's spectrum database)
these models are often not accurate. Ou aim is to enhance this database using crowd sourced measurements.


Project Idea:
==============

Collect spectrumavailibity data from avariety of sensor devices -> mobile phones, laptops, Raspberry pi etc. Develop an infrastucture to send these
data in an efficient and scabalble manner to a central database. We have for now created a mobile app. developments are underway to write drivers for raspberry pi and laptops.

Please refer to the project architecture PDF for details.


Technology Stack:
================

MqTT -> A publish-subscribe paradidm which is a lightweight alternative to HTTP, ideal for constrained devices with intermittent n/w connectivity.
We are using Hive mqtt as our broker

Client device app -> android/Python

Mongo -> Document DB for mesaurements

Django -> webserver for dashboard


How to use:
===========

Contributers have to download and insatll the Android App. The app will take care of sending data via Mqtt to the broker and 
listnening for incoming commands from the central controller. The client device needs to have network connectivity for this to work.

Dashboard:

The dashboard is the location where we can see the results of the data collectionas well as manually schedule scans on the cli3ent devices.

Current capabilities of dashboard :
1) The home page shows a region within which all the available devices and the average power measured in that region is showed. Drag the pointer on
the map to change the region, change the size of the circle to query differentregions.

2) The Heatmap page is just a visual representation of the signal strength ( aproxy for the presence/absence of a TV Channel at that location)

3) User Quipments page shows all the User equipemnts(currently onle cellular phones) that was connected to the system at some point of time, their model, their last known location. Clicking on the MAC Id
of the UEs will open the profile page of the UEs which will show info like, number of tyimes data sent, the average battery power etc. (somne of these features
are under development).


Once you install the app and start it you will see your phone come up in the UE list in the dashboard. (There is a refresh delay of 10secs which is programamble)
