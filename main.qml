import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15

    ApplicationWindow {
    visible: true
    color: "transparent"
    width: Screen.desktopAvailableWidth - 100
    height: Screen.desktopAvailableHeight - 100
        Component.onCompleted: {
        // Commenting this to use properties instead of setters
        //setX(Screen.width / 2 - width / 2);
        //setY(Screen.height / 2 - height / 2);
        x = Screen.width / 2 - width / 2
        y = Screen.height / 2 - height / 2
    }
    title: "Badge System"

    flags: Qt.FramelessWindowHint | Qt.WA_TranslucentBackground | Qt.Window

    property string version
    property string title
    
    property string currTime : "INITIALIZING..."
    
    property string odoostatus : "TCP/IP Pinging ODOO Server..."
    property string odoostatus_color : "gray"
    property string odooauthstatus : "XML Rpc Authing into ODOO Server..."
    property string odooauthstatus_color : "gray"

	property string rfid_area_color : "white"    
	property bool rfid_area_visible : true
    property string rfid_process_status : "Initializing..."
    property string rfid_process_status_color : "gray"
    
    property string rfid_action_text : "WAITING CARD"
    property string rfid_action_text_color : "black"
    property string rfid_card_text : "- - -"
    property string rfid_card_text_color : "black"
    property string rfid_date_text : "- - -"
    property string rfid_date_text_color : "black"
            
    property QtObject running_clock
    property QtObject odoopingcheck
    property QtObject odooauthcheck
    property QtObject rfid_process_check
    property QtObject rfidCheck

    Connections {
        target: rfidCheck
        function onRfidReset(msg) {
		if (msg) {
		rfid_area_color = "yellow"
		}
	}
	
	}

    Connections {
        target: rfidCheck
        function onRfidDate(msg) {
		rfid_date_text = msg
	}
        
    }

    Connections {
        target: rfidCheck
        function onRfidAction(msg) {
		rfid_action_text = msg
	}
        
    }

    Connections {
        target: rfidCheck
        function onRfidCardID(msg) {
		rfid_card_text = msg
	}
        
    }

    Connections {
        target: rfidCheck
        function onRfidCheckResult(msg) {
        if (!msg) {
            rfid_area_color = "red"
            rfid_area_visible = "false";}
        if (msg) {
            rfid_area_color = "green"
            rfid_area_visible = "true";}
        
    }
    
    }

    Connections {
        target: rfid_process_check
        function onIsRfidReaderRunning(msg) {
        if (!msg) {
            rfid_process_status = "RFID Reader NOT Running"
            rfid_process_status_color = "red";}
        if (msg) {
            rfid_process_status = "RFID Reader Running"
            rfid_process_status_color = "green";}
        
        
    }
    
    }

    Connections {
        target: running_clock
        function onTimetick(msg) {
        currTime = msg;
    }
    
    }
    Connections {
        target: odoopingcheck
        function onIsOdooUp(msg) {
        if (!msg) {
            odoostatus = "Odoo TCP/IP Ping FAILED"
            odoostatus_color = "red";}
        if (msg){
            odoostatus = "Odoo TCP/IP Ping SUCCESS"
            odoostatus_color = "green";}
        }
    }

    Connections {
        target: odooauthcheck
        function onIsOdooAuth(msg){
        if (!msg) {
            odooauthstatus = "Odoo Instance Auth FAILED"
            odooauthstatus_color = "red";}
        if (msg){
            odooauthstatus = "Odoo Instance Auth SUCCESS"
            odooauthstatus_color = "green";}
        }
    }

    Rectangle {
	color: "transparent"
        anchors.fill: parent

        Rectangle {
            anchors.fill: parent
            color: "transparent"

            Text {
                anchors {
                    top: parent.top
                    topMargin: 110
                    horizontalCenter: parent.horizontalCenter
                }
                text: currTime
                font.pixelSize: 64
                color: "white"
            }
            Text {
                anchors {
                    top: parent.top
                    topMargin: 15
                    left: parent.left
                    leftMargin: 15
                }
                text: title
                font.pixelSize: 16
                color: "white"
            }
            Text {
                anchors {
                    top: parent.top
                    topMargin: 45
                    left: parent.left
                    leftMargin: 15
                }
                text: version
                font.pixelSize: 16
                color: "white"
            }
            Text {
                anchors {
                    bottom: parent.bottom
                    bottomMargin: 75
                    left: parent.left
                    leftMargin: 15
                }
                text: "System status"
                font.pixelSize: 24
                color: "white"
            }
            Text {
                anchors {
                    bottom: parent.bottom
                    bottomMargin: 30
                    left: parent.left
                    leftMargin: 15
                }
                text: "Sqlite DB Local connection OK"
                font.pixelSize: 16
                color: "green"
            }

             Text {
                anchors {
                    bottom: parent.bottom
                    bottomMargin: 30
                    left: parent.left
                    leftMargin: 315
                }
                text: rfid_process_status
                font.pixelSize: 16
                color: rfid_process_status_color
            }

            Text {
                anchors {
                    bottom: parent.bottom
                    bottomMargin: 30
                    left: parent.left
                    leftMargin: 615
                }
                text: odoostatus
                font.pixelSize: 16
                color: odoostatus_color
            }

            Text {
                anchors {
                    bottom: parent.bottom
                    bottomMargin: 30
                    left: parent.left
                    leftMargin: 915
                }
                text: odooauthstatus
                font.pixelSize: 16
                color: odooauthstatus_color
            }

            Rectangle {
                id: tag
                visible: rfid_area_visible
                width: 200
                height: 200
                color: rfid_area_color
                anchors {
                    verticalCenter: parent.verticalCenter
                    right: parent.right
                    rightMargin: 100
                }
                Text {
                text: rfid_action_text
                font.pixelSize: 24
                anchors {
                horizontalCenter: parent.horizontalCenter
                top: parent.top
                topMargin: 45
                }
                }
                Text {
                text: rfid_card_text
                font.pixelSize: 20
                anchors {
                horizontalCenter: parent.horizontalCenter
                bottom: parent.bottom
                bottomMargin: 60
                }
                }
                Text {
                text: rfid_date_text
                font.pixelSize: 14
                anchors {
                horizontalCenter: parent.horizontalCenter
                bottom: parent.bottom
                bottomMargin: 25
                }
                }
            }
            }
        }

}
