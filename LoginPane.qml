import QtQuick
import QtQuick.Controls as Controls
import Quickshell.Io
import qs.Commons

Column {
    id: root
    property string python: ""
    property string base: ""
    property bool signedInAlready: false
    property bool refreshing: false
    property string phase: "idle"
    property string message: ""
    property bool cancelled: false
    readonly property bool authActive: auth.running
    readonly property color muted: Qt.rgba(Color.foreground.r,Color.foreground.g,Color.foreground.b,0.65)
    signal signedIn()
    spacing: 14
    function start() {
        if(auth.running || refreshing)return
        if(!email.acceptableInput || email.text.trim().indexOf("@")<1){message="Enter your Roborock account email address.";return}
        phase="starting";message="Starting sign-in…";cancelled=false;code.text="";auth.running=true
    }
    function verify() {
        if(phase!=="code_sent" || !code.acceptableInput){message="Enter the six-digit email code.";return}
        phase="verifying";message="Verifying your code…"
        auth.write(JSON.stringify({action:"verify",code:code.text})+"\n")
        code.text=""
    }
    function cancel() {
        cancelled=true
        if(auth.running)auth.running=false
        phase="idle";message="Sign-in cancelled.";code.text=""
    }
    Process {
        id: auth
        command: [root.python,"-u",root.base+"/omarock.py","auth"]
        stdinEnabled: true
        stdout: SplitParser {
            splitMarker: "\n"
            onRead: function(line) {
                try {
                    var event=JSON.parse(line)
                    if(event.state==="ready") {auth.write(JSON.stringify({action:"request",email:email.text.trim()})+"\n");return}
                    root.phase=event.state
                    root.message=event.message||""
                    if(event.state==="code_sent")Qt.callLater(function(){code.forceActiveFocus()})
                    if(event.state==="signed_in") {code.text="";email.text="";}
                }catch(e){root.phase="error";root.message="Could not read sign-in response. Cancel and try again."}
            }
        }
        // Consume, never echo or retain, authentication stderr.
        stderr: SplitParser { onRead: function(line) {} }
        onExited: function(exitCode) {
            code.text=""
            if(root.cancelled)return
            if(root.phase==="signed_in"){Qt.callLater(root.signedIn);return}
            if(root.phase!=="signed_in" && root.phase!=="error" && root.phase!=="expired") {root.phase="error";root.message="Sign-in stopped. Please try again."}
        }
    }
    Text {text:root.signedInAlready?"Connect another session":"Sign in to Roborock";font.family:Style.font.family;font.pixelSize:22;color:Color.foreground}
    Text {width:parent.width;text:"Use the email from your Roborock app. We’ll email a one-time code—no password or terminal required.";wrapMode:Text.WordWrap;font.family:Style.font.family;font.pixelSize:12;color:root.muted}
    Text {text:"ACCOUNT EMAIL";font.family:Style.font.family;font.pixelSize:10;color:root.muted}
    Controls.TextField {
        id: email
        objectName: "accountEmail"
        width: Math.min(parent.width,440)
        height: 42
        placeholderText: "you@example.com"
        color:Color.foreground
        placeholderTextColor:root.muted
        selectionColor:Color.accent
        selectedTextColor:Color.background
        font.family:Style.font.family
        font.pixelSize:13
        maximumLength:254
        readOnly:auth.running
        inputMethodHints:Qt.ImhEmailCharactersOnly | Qt.ImhNoPredictiveText
        Accessible.name:"Roborock account email"
        background:Rectangle {color:Qt.rgba(Color.foreground.r,Color.foreground.g,Color.foreground.b,0.055);radius:5;border.color:email.activeFocus?Color.accent:root.muted}
        onAccepted:root.start()
    }
    Row {
        spacing:10
        RockButton {text:root.phase==="starting" || root.phase==="requesting"?"Requesting…":"Send email code";primary:true;available:!auth.running && !root.refreshing;onClicked:root.start()}
        RockButton {text:"Cancel";visible:auth.running;onClicked:root.cancel()}
    }
    Column {
        width:parent.width
        spacing:12
        visible:root.phase==="code_sent" || root.phase==="verifying"
        Text {text:"VERIFICATION CODE";font.family:Style.font.family;font.pixelSize:10;color:root.muted}
        Controls.TextField {
            id: code
            objectName: "verificationCode"
            width:220
            height:42
            placeholderText:"6-digit code"
            echoMode:TextInput.Password
            maximumLength:6
            validator:RegularExpressionValidator {regularExpression:/[0-9]{6}/}
            inputMethodHints:Qt.ImhDigitsOnly | Qt.ImhSensitiveData | Qt.ImhNoPredictiveText
            enabled:root.phase==="code_sent"
            color:Color.foreground
            placeholderTextColor:root.muted
            selectionColor:Color.accent
            selectedTextColor:Color.background
            font.family:Style.font.family
            font.pixelSize:14
            Accessible.name:"Roborock verification code"
            background:Rectangle {color:Qt.rgba(Color.foreground.r,Color.foreground.g,Color.foreground.b,0.055);radius:5;border.color:code.activeFocus?Color.accent:root.muted}
            onAccepted:root.verify()
        }
        RockButton {text:root.phase==="verifying"?"Verifying…":"Sign in";primary:true;available:root.phase==="code_sent" && code.acceptableInput;onClicked:root.verify()}
    }
    Text {width:parent.width;text:root.message;visible:text!=="";wrapMode:Text.WordWrap;font.family:Style.font.family;font.pixelSize:12;color:Color.accent;Accessible.role:Accessible.AlertMessage}
    Text {width:parent.width;text:"Codes stay in memory and aren’t logged or stored. Your successful session is saved privately on this machine, outside the repository.";wrapMode:Text.WordWrap;font.family:Style.font.family;font.pixelSize:10;color:root.muted}
}
