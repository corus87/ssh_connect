from .app import SSHConnect

if __name__ == "__main__":
    try:
        SSHConnect().run()
    except KeyboardInterrupt:
        pass