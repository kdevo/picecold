Pyotek presents ...

![logo](.github/logo.png "PiceCold")

... transforming your Pi to a cold storage for your bitcoins

## Requirements
- Raspberry Pi (Zero, B+, 2 or 3)
- Display: Display-O-Tron HAT or Display-O-Tron 3K (dot3k)
- A good security understanding regarding your private keys
- A cup of :coffee: for carefully following the initial [Installation](#installation)

## Installation
> :warning: Sorry, installation instructions are not noob-proof yet!
> Currently, they are also *completely untested* and flushed from my memory after implementing PiceCold.

1. Install dependencies:
	- `sudo apt install python3 python-pip`
2. Install [dot3k](https://github.com/pimoroni/dot3k)
3. Install and configure Electrum:
    - Refer to [the official instructions](https://electrum.org/#download) for installation
    - **Kill all possible internet connections! You need to be absolutely sure that you are completely offline to continue!** 
    - [Follow cold storage instructions](http://docs.electrum.org/en/latest/coldstorage.html) (you need to use your Pi via mouse & keyboard)
4. Install and configure PiceCold:
    - Download and extract this project to a USB stick *by using your normal online PC*, then copy to `/home/pi/PiceCold` on your *offline Raspberry Pi*
    - Configure `/home/pi/PiceCold/example_usage/picecold.ini`
    - Test the user interface via `cd /home/pi/PiceCold/example_usage && ./start.py`
    - Install provided systemd service example in `/home/pi/PiceCold/example_usage/systemd`
5. Test and verify if installation was successful:
    - Create a (dummy) unsigned transaction ([see here](http://docs.electrum.org/en/latest/coldstorage.html#create-an-unsigned-transaction))
    - Put it on a USB stick
    - Plug USB stick in the **Pi**ceCold:
        - "Trust" USB stick
        - Sign TX
    - Optional - only if you really want to send the transaction (**this cannot be undone**): [Broadcast TX](http://docs.electrum.org/en/latest/coldstorage.html#broadcast-your-transaction)

## Security

The whole point of a cold storage is that the **device (your Pi) needs to be offline the whole time** after the Electrum installation.

Because there is no encryption of the password to unlock your wallet involved in [picecold.ini](./example_usage/picecold.ini), it is a security requirement to keep your **Pi**ceCold as safe as a paper wallet with your private keys on it!

(This might change in a future release...)

## FAQ

...