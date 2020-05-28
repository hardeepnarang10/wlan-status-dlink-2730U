# Fetch function
from requests import get
from bs4 import BeautifulSoup

# Read configuration file
from configparser import ConfigParser

# Timeloop Wrapper
from timeloop import Timeloop
from datetime import timedelta


class DLink2730URouterStatus:

    def __init__ ( self ):

        # Parse config.ini
        self.CONFIG_PATH = "./config.ini"

        self.config = ConfigParser()
        self.config.read(self.CONFIG_PATH)

        self.configuration = self.config.sections()[0]

        self.platform = self.config.get(self.configuration, 'platform').lower()
        self.router_user = self.config.get(self.configuration, 'router_user')
        self.router_pass = self.config.get(self.configuration, 'router_pass')

        # Reference Map : ( status , color style - console output , router string* )
        self.connection_status = (
            ( "Online" , "\033[32m" , "Up" ) ,
            ( "Offline" , "\033[31m" , "Down" ) ,
            ( "Disconnected" , "\033[33m" )
            )
        
        self.color_reset = "\033[m" # Reset console color
        self.ignore = 404 # Report this code in case of error - notifier will ignore this

        # Buffer last reported code to this container
        self.buffer = self.ignore # Initialize container to ignore default code

        self.duration = 3 # Notification and timeloop

        self.ICON_PATH = "./wlan.ico"

        # Platform-specific notifier:

        if self.platform == "windows":

            # Import 'Windows 10' Toast module:
            from win10toast import ToastNotifier

            # Instantiate
            self.notifier_windows = ToastNotifier()

        elif self.platform == "linux":

            # Import 'Linux Desktop Notification' module (Tested on Debian 10 Buster):
            from notify2 import init, Notification

            # Instantiate
            self.notifier_linux = init( "DLink-2730U Router Connection Status Notifier" )
            self.n = Notification( "Connection Status" , message = "Daemon Running" , icon = self.ICON_PATH )

    # Todo: Fetch and parse router page
    # Return: Connection code
    def get_connection_status( self ):

        try:
            status_page = get( "http://192.168.1.1/status.htm" ,
                            auth = ( self.router_user , self.router_pass )
                            ).content
        # Disconnected
        except OSError:
            return 2

        status_page_parsed = BeautifulSoup( status_page , "html.parser" )

        try:
            status_text = status_page_parsed.find_all( "font" ) [7].text

            # Check online & offline values in connection_status
            for index , status in enumerate( self.connection_status[:-1] ) :
                if status[-1] in status_text : return index

        except IndexError:
            return self.ignore

    # Todo: Notify connection status
    def notify( self , index ):

        print( f"{ self.connection_status[ index ][ 1 ] }{ self.connection_status[ index ][ 0 ] }" , self.color_reset )

        if self.platform == "windows":
            self.notifier_windows.show_toast ( title = "" , msg = f"Connection Status: { self.connection_status[ index ][ 0 ] }" , duration = self.duration , icon_path = self.ICON_PATH ) 

        elif self.platform == "linux":
            self.n.update(f"Connection Status: { self.connection_status[ index ][ 0 ] }", icon = self.ICON_PATH)
            self.n.show()


router = DLink2730URouterStatus()

# Todo: Start timeloop
timeloop = Timeloop()

@timeloop.job ( interval = timedelta ( seconds = router.duration ) )
def status_notifier():
    
    status = router.get_connection_status()

    # Already reported OR encounter error
    if ( ( router.buffer == status ) or ( status == router.ignore ) ) :
        pass
    # Success
    else:
        router.notify ( status )

        # Update buffer
        router.buffer = status


# Invoke timeloop
if __name__ == "__main__": timeloop.start ( block = True )
