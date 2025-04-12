from eyes import Eyes, EyesPosition, EyesMood
from time import sleep

def main():
    eyes = Eyes()
    eyes.open()
    # eyes.set_idle(True)

    while True:
        eyes.set_mood(EyesMood.NEUTRAL)
        sleep(5)
        eyes.set_mood(EyesMood.ANGRY)
        sleep(3)
        eyes.set_mood(EyesMood.SAD)
        sleep(3)
        eyes.set_mood(EyesMood.TIRED)
        sleep(3)
        eyes.set_mood(EyesMood.HAPPY)
        sleep(3)
        eyes.set_position(EyesPosition.TOP_LEFT)
        sleep(3)
        eyes.set_position(EyesPosition.BOTTOM_RIGHT)
        sleep(3)
        eyes.set_position(EyesPosition.CENTER)
        sleep(3)


if __name__ == "__main__":
    main()
