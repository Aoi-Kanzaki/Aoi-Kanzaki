import os
import sys
import json
import pip
import time
import subprocess
try:
    from colr import color
except:
    print("Colr module is not installed, installing...")
    time.sleep(2)
    pip.main(["install", "colr"])
    from colr import color

colors = {
    "blue": (4, 95, 185),
    "cyan": (4, 211, 232),
    "purple": (123, 4, 232),
    "green": (4, 232, 95),
    "red": (189, 16, 16),
    "yellow": (163, 187, 3),
    "grey": (110, 108, 108)
}


def clear_screen():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


clear_screen()
if not os.path.exists("config.json"):
    with open("config.json", "w") as f:
        parse = json.loads('{"prefix": "None", "guildid": "None", "token": "None", "spotify_id": "None", "spotify_secret": "None", "mongoURI": "None"}')
        f.write(json.dumps(parse, indent=4, sort_keys=True))
        f.truncate()


def intro():
    print(color("+----------------------------------------------+", fore=colors["blue"]))
    print(color("Fresh Launcher", fore=colors["blue"]))
    print(color("Github: https://github.com/JonnyBoy2000/Fresh", fore=colors["blue"]))
    print(color("If you have any questions, open the link above.", fore=colors["blue"]))
    print(color("+----------------------------------------------+", fore=colors["blue"]))


def main_menu():
    while True:
        intro()
        print(color("\nMain Menu:", fore=colors["green"]))
        print(color("1.", fore=colors["cyan"]), color(" Run Fresh", fore=colors["purple"]))
        print(color("2.", fore=colors["cyan"]), color(" Setup Config", fore=colors["purple"]))
        print(color("3.", fore=colors["cyan"]), color(" Install Requirements", fore=colors["purple"]))
        print(color("4.", fore=colors["cyan"]), color(" Exit", fore=colors["purple"]))
        print(color("\nPlease input a number between 1-3 to select the option. Or 4 to quit.", fore=colors["green"]))
        choice = input(color("⤷ ", fore=colors["red"])).lower().strip()
        if choice == "1":
            interpreter = sys.executable
            cmd = (interpreter, "main.py")
            while True:
                try:
                    code = subprocess.call(cmd)
                except KeyboardInterrupt:
                    clear_screen()
                    code = 0
                    break
                else:
                    if code == 0:
                        clear_screen()
                        break
        elif choice == "2":
            setup_menu()
        elif choice == "3":
            print(color("Getting req.txt, then installing dependencies...", fore=colors["green"]))
            time.sleep(2)
            clear_screen()
            pip.main(["install", "-r", "req.txt"])
            clear_screen()
        elif choice == "4":
            clear_screen()
            exit()
        else:
            input(color("\nInvalid choice. Press enter to continue.", fore=colors["red"]))


def setup_menu():
    clear_screen()
    while True:
        intro()
        print(color("\nSetup Menu:", fore=colors["green"]))
        print(color("1.", fore=colors["cyan"]), color(" Setup Token", fore=colors["purple"]))
        print(color("2.", fore=colors["cyan"]), color(" Setup Guild ID", fore=colors["purple"]))
        print(color("3.", fore=colors["cyan"]), color(" Setup Prefix", fore=colors["purple"]))
        print(color("4.", fore=colors["cyan"]), color(" Setup Spotify Client ID", fore=colors["purple"]))
        print(color("5.", fore=colors["cyan"]), color(" Setup Spotify Client Secret", fore=colors["purple"]))
        print(color("6.", fore=colors["cyan"]), color(" Setup Mongo URI", fore=colors["purple"]))
        print(color("7.", fore=colors["cyan"]), color(" Back", fore=colors["purple"]))
        print(color("\nPlease input a number between 1-6 to change the config. Or 7 to go back to the main menu.", fore=colors["green"]))
        choice = input(color("⤷ ", fore=colors["red"])).lower().strip()
        if choice == "1":
            token = input(color("\nPlease enter your bot's token:\n➣ ", fore=colors["green"]))
            change_config("token", token)
        elif choice == "2":
            guildid = input(color("\nPlease enter your guild id:\n➣ ", fore=colors["green"]))
            change_config("guildid", guildid)
        elif choice == "3":
            prefix = input(color("\nPlease enter your desired prefix:\n➣ ", fore=colors["green"]))
            change_config("prefix", prefix)
        elif choice == "4":
            spotifyid = input(color("\nPlease enter your Spotify Client ID:\n➣ ", fore=colors["green"]))
            change_config("spotify_id", spotifyid)
        elif choice == "5":
            spotifysecret = input(color("\nPlease enter your Spotify Client Secret:\n➣ ", fore=colors["green"]))
            change_config("spotify_secret", spotifysecret)
        elif choice == "6":
            mongouri = input(color("\nPlease enter your MongoURI, or you can say off to disable:\n➣ ", fore=colors["green"]))
            change_config("mongoURI", mongouri)
        elif choice == "7":
            clear_screen()
            main_menu()
        else:
            input(color("\nInvalid choice. Press enter to continue.", fore=colors["red"]))
        clear_screen()


def change_config(key, value):
    if value == "":
        return input(color("\nYou cannot set the config option as nothing. Press enter to continue.", fore=colors["red"]))
    else:
        with open("config.json", "r+") as f:
            settings = json.load(f)
            if value in ["off", "Off"]:
                if key not in ["mongoURI"]:
                    return input(color("You cannot disabled this config option. Press enter to continue.", fore=colors["red"]))
                else:
                    value = "Disabled."
            if settings[key] == value:
                if key in ["mongoURI"]:
                    return input(color("You can't disable somthing that is already disabled. Press enter to continue.", fore=colors["red"]))
                return input(color("You cannot set the config settings to the same value. Press enter to continue.", fore=colors["red"]))
            settings[key] = value
            f.seek(0)
            f.write(json.dumps(settings, indent=4, sort_keys=True))
            f.truncate()
            clear_screen()

if __name__ == "__main__":
    main_menu()
