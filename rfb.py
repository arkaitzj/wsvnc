"""
RFB protocol implementattion, client side.

Override RFBClient and RFBFactory in your application.
See vncviewer.py for an example.

(C) 2003 cliechti@gmx.net

MIT License
"""

from struct import pack, unpack

#encoding-type
#for SetEncodings()
RAW_ENCODING =                  0
COPY_RECTANGLE_ENCODING =       1
RRE_ENCODING =                  2
CORRE_ENCODING =                4
HEXTILE_ENCODING =              5
ZLIB_ENCODING =                 6
TIGHT_ENCODING =                7
ZLIBHEX_ENCODING =              8 
ZRLE_ENCODING =                 16
POINTERPOS    =                 -232
#0xffffff00 to 0xffffffff tight options

#keycodes
#for KeyEvent()
KEY_BackSpace = 0xff08
KEY_Tab =       0xff09
KEY_Return =    0xff0d
KEY_Escape =    0xff1b
KEY_Insert =    0xff63
KEY_Delete =    0xffff
KEY_Home =      0xff50
KEY_End =       0xff57
KEY_PageUp =    0xff55
KEY_PageDown =  0xff56
KEY_Left =      0xff51
KEY_Up =        0xff52
KEY_Right =     0xff53
KEY_Down =      0xff54
KEY_F1 =        0xffbe
KEY_F2 =        0xffbf
KEY_F3 =        0xffc0
KEY_F4 =        0xffc1
KEY_F5 =        0xffc2
KEY_F6 =        0xffc3
KEY_F7 =        0xffc4
KEY_F8 =        0xffc5
KEY_F9 =        0xffc6
KEY_F10 =       0xffc7
KEY_F11 =       0xffc8
KEY_F12 =       0xffc9
KEY_F13 =       0xFFCA
KEY_F14 =       0xFFCB
KEY_F15 =       0xFFCC
KEY_F16 =       0xFFCD
KEY_F17 =       0xFFCE
KEY_F18 =       0xFFCF
KEY_F19 =       0xFFD0
KEY_F20 =       0xFFD1
KEY_ShiftLeft = 0xffe1
KEY_ShiftRight = 0xffe2
KEY_ControlLeft = 0xffe3
KEY_ControlRight = 0xffe4
KEY_MetaLeft =  0xffe7
KEY_MetaRight = 0xffe8
KEY_AltLeft =   0xffe9
KEY_AltRight =  0xffea

KEY_Scroll_Lock = 0xFF14
KEY_Sys_Req =   0xFF15
KEY_Num_Lock =  0xFF7F
KEY_Caps_Lock = 0xFFE5
KEY_Pause =     0xFF13
KEY_Super_L =   0xFFEB
KEY_Super_R =   0xFFEC
KEY_Hyper_L =   0xFFED
KEY_Hyper_R =   0xFFEE

KEY_KP_0 =      0xFFB0
KEY_KP_1 =      0xFFB1
KEY_KP_2 =      0xFFB2
KEY_KP_3 =      0xFFB3
KEY_KP_4 =      0xFFB4
KEY_KP_5 =      0xFFB5
KEY_KP_6 =      0xFFB6
KEY_KP_7 =      0xFFB7
KEY_KP_8 =      0xFFB8
KEY_KP_9 =      0xFFB9
KEY_KP_Enter =  0xFF8D

class RFBClient(object):
    
    def __init__(self,transport):
        self._packet = []
        self._packet_len = 0
        self._already_expecting = 0
        self.transport = transport
        self.do_handshake()
        self.rectangles = []

    def fileno(self):
        return self.transport.fileno()

    def do_handshake(self):
        buff = self.transport.recv(12)
        if '\n' in buff:
            if buff[:3] == 'RFB':
                maj, min = [int(x) for x in buff[3:-1].split('.')]
                if (maj, min) not in [(3,3), (3,7), (3,8)]:
                    raise Exception("wrong protocol version\n") 
            self.version = "%d.%d"%(maj,min)
            self.transport.send('RFB 003.003\n')
            print("connected with version %s"%(self.version))
            self.handle_auth()
            # Shared flag to 0,exclusive access to this vnc server
            self.transport.sendall(pack("!B", 0))
            self.handle_server_init()
            print "bpp:%d depth:%d bigendian:%d truecolor:%d redmax:%d greenmax:%d bluemax:%d redshift:%d greenshift:%d blueshift:%d"%(self.bpp, self.depth,self.bigendian,self.truecolor,self.redmax,self.greenmax,self.bluemax,self.redshift,self.greenshift,self.blueshift)
#            self.set_pixel_format(bpp=self.bpp, depth=self.depth, bigendian=self.bigendian, truecolor=self.truecolor, redmax=self.redmax, greenmax=self.greenmax, bluemax=self.bluemax, redshift=self.redshift, greenshift=self.greenshift, blueshift=self.blueshift)
            self.set_pixel_format()
            self.set_encodings([RAW_ENCODING, POINTERPOS])

        else:
            raise Exception("Weird error")
    def get_info(self):
        return (self.name,self.width,self.height)
    
    def handle_auth(self):
        block = self.transport.recv(4)
        (auth,) = unpack("!I", block)
        if auth == 0:
            raise Exception("Server issued an invalid security type")
        elif auth == 1:
            #No auth required
            return
        elif auth == 2:
            self.expect(self._handleVNCAuth, 16)
        else:
            raise Exception("unknown auth response (%d)\n" % auth)

    def handle_server_init(self):
        block = self.transport.recv(24)
        (self.width, self.height, pixformat, namelen) = unpack("!HH16sI", block)
        print "Found %s"%(str((self.width, self.height, pixformat, namelen)))
        block = self.transport.recv(namelen)
        (self.name,) = unpack("!%ds"%(namelen),block)
        print "Name is: %s"%(self.name)
        (self.bpp, self.depth, self.bigendian, self.truecolor, 
         self.redmax, self.greenmax, self.bluemax,
         self.redshift, self.greenshift, self.blueshift) = \
           unpack("!BBBBHHHBBBxxx", pixformat)
        self.bypp = self.bpp / 8        #calc bytes per pixel



#    def _handleVNCAuth(self, block):
#        self._challenge = block
#        self.vncRequestPassword()
#        self.expect(self._handleVNCAuthResult, 4)

#    def sendPassword(self, password):
#        """send password"""
#        pw = (password + '\0' * 8)[:8]        #make sure its 8 chars long, zero padded
#        #~ des = Crypto.Cipher.DES.new(pw)
#        #~ response = des.encrypt(challenge)
#        des = crippled_des.DesCipher(pw)
#        response = des.encrypt(self._challenge[:8]) +\
#                   des.encrypt(self._challenge[8:])
#        self.transport.write(response)

    def receive(self):
        block = self.transport.recv(2)
        (msgid,padding) = unpack("!BB", block)
        if padding != 0:
            print "msg:%d"%(padding)
        if msgid == 0:
            rectangles = self.handle_framebuffer_update()
            return (0,rectangles)
        elif msgid == 2:
            return (msgid,None)
        elif msgid == 3:
            print "cutText"
        else:
            raise Exception("Unknown message received, id:%d"%(msgid))

    def handle_framebuffer_update(self):
        block = self.transport.recv(2)
        (rectanglecount,) = unpack("!H", block)
        rectangles = []
        for i in range(rectanglecount):
            block = self.transport.recv(12)
            (x,y,w,h,encoding) = unpack("!HHHHI",block)

            if encoding == COPY_RECTANGLE_ENCODING:
                print "COPY_RECTANGLE_ENCODING"
#                self.expect(self._handleDecodeCopyrect, 4, x, y, width, height)
            elif encoding == RAW_ENCODING:
                total_size = w*h*self.bypp
                rectanglebytes = ''
                curlen = 0
                while curlen < total_size :
                    rectanglebytes += self.transport.recv(total_size-curlen)
                    curlen = len(rectanglebytes)
                rectangles.append(dict({'x':x,'y':y,'width':w,'height':h,'encoding':'Raw','data':rectanglebytes}))
#                self.expect(self._handleDecodeRAW, width*height*self.bypp, x, y, width, height)
            elif encoding == HEXTILE_ENCODING:
                print "HEXTILE_ENCODING" 
#                self._doNextHextileSubrect(None, None, x, y, width, height, None, None)
            elif encoding == CORRE_ENCODING:
                print "CORRE_ENCODING"
#                self.expect(self._handleDecodeCORRE, 4 + self.bypp, x, y, width, height)
            elif encoding == RRE_ENCODING:
                print "RRE_ENCODING"
#                self.expect(self._handleDecodeRRE, 4 + self.bypp, x, y, width, height)
            else:
                raise Exception("unknown encoding received (encoding %d)\n" % encoding)
        return rectangles



    # Client->Server
    def framebuffer_update_request(self, x=0, y=0, width=None, height=None, incremental=0):
        if width  is None: width  = self.width - x
        if height is None: height = self.height - y
        self.transport.send(pack("!BBHHHH", 3, incremental, x, y, width, height))


    
#    def _handleVNCAuthResult(self, block):
#        (result,) = unpack("!I", block)
#        #~ print "auth:", auth
#        if result == 0:     #OK
#            self._doClientInitialization()
#            return
#        elif result == 1:   #failed
#            self.vncAuthFailed("autenthication failed")
#            self.transport.loseConnection()
#        elif result == 2:   #too many
#            slef.vncAuthFailed("too many tries to log in")
#            self.transport.loseConnection()
#        else:
#            log.msg("unknown auth response (%d)\n" % auth)
#        
        
#    def _handleDecodeCopyrect(self, block, x, y, width, height):
#        (srcx, srcy) = unpack("!HH", block)
#        self.copyRectangle(srcx, srcy, x, y, width, height)
#        self._doConnection()
#        
    # ---  other server messages
    
#    def _handleServerCutText(self, block):
#        (length, ) = unpack("!xxxI", block)
#        self.expect(self._handleServerCutTextValue, length)
#    
#    def _handleServerCutTextValue(self, block):
#        self.copy_text(block)
#        self.expect(self._handleConnection, 1)
    
    #------------------------------------------------------
    # client -> server messages
    #------------------------------------------------------
    
    def set_pixel_format(self, bpp=32, depth=24, bigendian=0, truecolor=1, redmax=255, greenmax=255, bluemax=255, redshift=0, greenshift=8, blueshift=16):
        pixformat = pack("!BBBBHHHBBBxxx", bpp, depth, bigendian, truecolor, redmax, greenmax, bluemax, redshift, greenshift, blueshift)
        self.transport.send(pack("!Bxxx16s", 0, pixformat))
        #rember these settings
        self.bpp, self.depth, self.bigendian, self.truecolor = bpp, depth, bigendian, truecolor
        self.redmax, self.greenmax, self.bluemax = redmax, greenmax, bluemax
        self.redshift, self.greenshift, self.blueshift = redshift, greenshift, blueshift
        self.bypp = self.bpp / 8        #calc bytes per pixel
        #~ print self.bypp

    def set_encodings(self, list_of_encodings):
        self.transport.send(pack("!BxH", 2, len(list_of_encodings)))
        for encoding in list_of_encodings:
            self.transport.send(pack("!i", encoding))
    
    def key_event(self, key, down=1):
        """For most ordinary keys, the "keysym" is the same as the corresponding ASCII value.
        Other common keys are shown in the KEY_ constants."""
        self.transport.send(pack("!BBxxI", 4, down, key))

    def mouse(self,x,y,left=0,right=0):
        buttonmask = 0
        if left:
            buttonmask |= 0x01
        if right:
            buttonmask |= 0x03
        self.transport.send(pack("!BBhh", 5, buttonmask, x, y))

#    def clientCutText(self, message):
#        """The client has new ASCII text in its cut buffer.
#           (aka clipboard)
#        """
#        self.transport.write(pack("!BxxxI", 6, len(message)) + message)
