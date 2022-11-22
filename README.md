<p align="center">
  <a href="https://github.com/JonnyBoy2000/Kira-Miki">
    <img src="gh_banner.jpg" width="1000" height="200">
  </a>
  <p align="center">
    A multi purpose Discord bot. Made by Jonny with ❤!
    <br/>
    <a href="https://discord.gg/qRt2NbAtq2">Discord Support</a>
    |
    <a href="https://discord.com/oauth2/authorize?client_id=834979964062662656&scope=bot+applications.commands">Public Invite Link</a>
  </p>
</p>

## Table of Contents

- [About the Project](#about-the-project)
  - [Built With](#built-with)
- [Getting Started](#getting-started)
  - [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
  - [Developer?](#developer)
  - [Not a Developer?](#not-a-developer-but-still-want-to-help-out)
- [License](#license)
- [Contact](#contact)

## About The Project

Aoi Kanzaki is a Multi-Function discord bot that I have been working on for a while. I have created other projects such as Brooklyn Bot, Kira-Miki and more.
Aoi contains a ton of features, from music to leveling and more. (More will be added.)

### Built With

Here you will find some things you will need.

- [Lavalink.py](https://github.com/JonnyBoy2000/Lavalink.py)
- [Lavlink.jar](https://github.com/Frederikam/Lavalink)
- [Discord.py Rewrite](https://github.com/Rapptz/discord.py/)
- [Python3.6+](https://www.python.org/)
- [MongoDb](https://docs.mongodb.com/)
- [Java Oracle](https://www.oracle.com/java/)

## Getting Started

Read to install and setup? No problem! That's what this part of the page is for.

### Installation

1. Install python if you don't have it already. (Make sure to install version 3.6 or later)
2. Install java also if you don't have it
3. Install and setup mongodb you can do so here.

```
Windows: https://docs.mongodb.com/manual/tutorial/install-mongodb-on-windows/
Linux: https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/
Others: There is a list at the top of the page. (https://docs.mongodb.com/manual/tutorial/)
```

4. You're going to need a Spotify api key for the music module.

```
You should be able to get one here. https://developer.spotify.com/web-api/
```

5. Clone the repo

```sh
git clone https://github.com/Aoi-Kanzaki/Aoi-Kanzaki.git
```

6. Move into the bots directory

```sh
cd Aoi-Kanzaki
```

7. Install requirements

```sh
sudo python3 -m pip install -r requirements.txt
```

8. Rename `config.json.example` to `config.json` and set prefix as the prefix you want, and token as your bots token.

9. Create a lavalink folder and download the lavalink server. https://github.com/freyacodes/Lavalink/releases/download/3.6.2/Lavalink.jar

10. You will also need a `application.yml` for your lavalink server. You can get one here. https://github.com/freyacodes/Lavalink/blob/master/LavalinkServer/application.yml.example

11. Start a screen session, press enter, and type the following command to startup the Lavalink server for music.

```sh
screen
(press enter)
sudo java -jar Lavalink.jar
```

11. Disconnect from the screen session by pressing ctrl+A+D
12. Now you should be able to run the bot! Just type the following command!

```sh
cd .. && python3 bot.py
```

## Usage

<p>
  Now how do I use the bot? Well it's simple.
  <br/>
  Every command is a slash command so all you will need to do is type `/` and it will autocomeplete for you.
  <br/>
  To get all of the bots commands use the following <b>/help</b>.
  <br/>
  If you are wanting help on a specific module use the following <b>/help ModuleName</b>.
  <br/>
  Also if you're wanting help on a specific command use the following <b>/help CommandName</b>.
</p>

## Contributing

Want to help out an contribute? Keep in mind that any contributions you make are **greatly appreciated**.

### Developer?

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Not a developer but still want to help out?

<p>
  That's okay, you can head over to my patreon, or my paypal.
  <br/>
  CashApp: `$jonnylokken0`
</p>

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

<p>
  You can join the Discord support server at the top of this page.
  <br/>
  You can also email me at jonathonlokken54@gmail.com
  <br/>
  I might give you more options to contact me, but not right now.
</p>
