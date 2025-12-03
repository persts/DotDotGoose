// This is the SIP interface definition for the std::optional mapped type.
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


%If (Qt_6_7_0 -)

template<_TYPE_>
%MappedType std::optional<_TYPE_> /TypeHint="Optional[_TYPE_]"/
{
%TypeHeaderCode
#include <optional>
%End

%ConvertFromTypeCode
    if (!sipCpp->has_value())
    {
        Py_INCREF(Py_None);
        return Py_None;
    }

    _TYPE_ *t = new _TYPE_(sipCpp->value());

    PyObject *tobj = sipConvertFromNewType(t, sipType__TYPE_, sipTransferObj);

    if (!tobj)
    {
        delete t;

        return 0;
    }

    return tobj;
%End
};

%End
