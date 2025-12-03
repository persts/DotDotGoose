// This is the SIP interface definition for the QByteArrayView mapped type.
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


%MappedType QByteArrayView /TypeHint="QByteArray"/
{
%TypeHeaderCode
#include <qbytearrayview.h>
%End

%ConvertToTypeCode
if (sipIsErr == NULL)
{
    // Note that we choose to use QByteArray's implementation of the buffer
    // protocol.
    return sipGetBufferInfo(sipPy, NULL);
}

sipBufferInfoDef *buffer_info = (sipBufferInfoDef *)sipMalloc(
        sizeof (sipBufferInfoDef));

if (buffer_info)
{
    if (sipGetBufferInfo(sipPy, buffer_info) > 0)
    {
        // Check that the buffer is compatible with one defined by
        // PyBuffer_FillInfo() as used by QByteArray and the standard Python
        // byte objects.
        if (buffer_info->bi_format == NULL || buffer_info->bi_format[0] == 'B')
        {
            *sipCppPtr = new QByteArrayView(
                    reinterpret_cast<const unsigned char *>(
                            buffer_info->bi_buf),
                    (qsizetype)buffer_info->bi_len);

            *sipUserStatePtr = buffer_info;

            // We don't support transfer of ownership.
            return SIP_TEMPORARY;
        }

        PyErr_Format(PyExc_TypeError, "unsupported buffer format '%s'",
                buffer_info->bi_format);

        sipReleaseBufferInfo(buffer_info);
    }

    sipFree(buffer_info);
}

*sipIsErr = 1;

return 0;
%End

%ReleaseCode
delete sipCpp;

sipBufferInfoDef *buffer_info = reinterpret_cast<sipBufferInfoDef *>(sipUserState);
sipReleaseBufferInfo(buffer_info);
sipFree(buffer_info);
%End
};
