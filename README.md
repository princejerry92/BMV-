# BMV-Emitter
 A forex trading software that uses flask-SocketIO  as its backend to connect to MT5 API retrieves trade informations and signal from a mother bot and broadcast it to all users of the software
and to Telegram app , the whatsapp feature will be on the next update . It also features a GUI that will be bundled with electron.js so that it can be easily installed 
. on this day 16/07/2024 turn it into an exec , well after 7 failed attempt, pyinstaller kept missing the async modules needed to run it and kept popping invalis async mode error . this was resolved by switching to a production server and using gevent , when you do import all submodles of the gevent then specify expilictly the async mode , this helps , 
