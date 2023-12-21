This is a telegram bot that helps users search for cards on deckbox.org and scryfall.com

For local setup:
* Create a bot in telegram by messaging @BotFather and deckbox.org account
* Install docker
* Create an .env file by using .env.template and entering your bot token and deckbox.org credentials
* Make build_docker_images executable by using ```chmod +x build_docker_images.sh```
* Run the script by using ```./build_docker_images.sh``` to buid docker images
* In the /docker directory use ```docker compose up -d```
* Send any message to the bot