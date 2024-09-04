from PySide6.QtDesigner import QPyDesignerCustomWidgetCollection

from kalao.guis.utils.parts import FindPart, ImgMinMaxPart

FindPart_ui = \
"""
<ui>
    <class>FindPart</class>
    <widget class="FindPart" name="widget" native="true">
    </widget>
</ui>
"""

QPyDesignerCustomWidgetCollection.registerCustomWidget(
    FindPart, module="kalao.guis.utils.parts", tool_tip="FindPart",
    xml=FindPart_ui)

ImgMinMaxPart_ui = \
"""
<ui>
    <class>ImgMinMaxPart</class>
    <widget class="ImgMinMaxPart" name="widget" native="true">
    </widget>
</ui>
"""

QPyDesignerCustomWidgetCollection.registerCustomWidget(
    ImgMinMaxPart, module="kalao.guis.utils.parts", tool_tip="ImgMinMaxPart",
    xml=ImgMinMaxPart_ui)
