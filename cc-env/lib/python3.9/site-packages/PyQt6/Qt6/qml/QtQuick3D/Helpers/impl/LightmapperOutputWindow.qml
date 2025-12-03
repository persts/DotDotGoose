// Copyright (C) 2023 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    anchors.fill: parent

    function appendText(text: string) {
        textArea.insert(textArea.length, text + "\n")
    }

    ColumnLayout {
        anchors.fill: parent
        Button {
            objectName: "cancelButton"
            Layout.fillWidth: true
            text: "Cancel"
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            TextArea {
                id: textArea
                readOnly: true
                placeholderText: qsTr("Qt Lightmapper")
                font.pixelSize: 12
                wrapMode: Text.WordWrap
            }
        }
    }
}
