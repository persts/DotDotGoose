// This is the SIP interface definition for the QChar mapped types.
//
// Copyright (c) 2024 Riverbank Computing Limited <info@riverbankcomputing.com>
// 
// This file is part of PyQt6.
// 
// This file may be used under the terms of the GNU General Public License
// version 3.0 as published by the Free Software Foundation and appearing in
// the file LICENSE included in the packaging of this file.  Please review the
// following information to ensure the GNU General Public License version 3.0
// requirements will be met: http://www.gnu.org/copyleft/gpl.html.
// 
// If you do not wish to use this file under the terms of the GPL version 3.0
// then you may purchase a commercial license.  For more information contact
// info@riverbankcomputing.com.
// 
// This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
// WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.


%MappedType QChar /TypeHint="str",TypeHintValue="''"/
{
%TypeHeaderCode
#include <qchar.h>
%End

%ConvertToTypeCode
if (sipIsErr == NULL)
    return PyUnicode_Check(sipPy);

// TODO: review replacing with something more efficient.
QString qs = qpycore_PyObject_AsQString(sipPy);

if (qs.size() != 1)
{
    PyErr_SetString(PyExc_ValueError, "string of length 1 expected");
    *sipIsErr = 1;
    return 0;
}

*sipCppPtr = new QChar(qs.at(0));

return sipGetState(sipTransferObj);
%End

%ConvertFromTypeCode
    // TODO: replace with...
    // return PyUnicode_FromKindAndData(PyUnicode_2BYTE_KIND, sipCpp, 1);
    return qpycore_PyObject_FromQString(QString(*sipCpp));
%End
};
