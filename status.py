# Fetch function
from requests import get
from bs4 import BeautifulSoup

# Notify function
from win10toast import ToastNotifier

# Timeloop Wrapper
from timeloop import Timeloop
from datetime import timedelta


class Win10RouterStatus:

    def __init__ ( self ):

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
        self.notifier = ToastNotifier()


    # Todo: Fetch and parse router page
    # Return: Connection code
    def get_connection_status( self ):

        try:
            status_page = get( "http://192.168.1.1/status.htm" ,
                            auth = ("<router_username>" , "<router_password>" )
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

        self.notifier.show_toast ( title = "" , msg = f"Connection Status: { self.connection_status[ index ][ 0 ] }" , duration = self.duration , icon_path = "wlan.ico" ) 


router = Win10RouterStatus()

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
