"""Indicadores agregados del propietario; sin calcular reglas de negocio."""
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (QDateTimeEdit, QDialog, QFormLayout, QHBoxLayout, QLabel,
                               QPushButton, QScrollArea, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget, QHeaderView)

from .client import ApiError, ContractError
from .session_context import OperationContext

SERIES=(
    ('inventario','Inventario por estado'),
    ('receptores','Solicitudes por estado'),
    ('inventario','Caducidades por estado'),
    ('transporte','Recolección a aceptación'),
)
SERVICES={
    'OPERATOR':('inventario','receptores','transporte'),
    'MEDICAL':('inventario','receptores','transporte'),
    'COORDINATOR':('inventario','transporte'),
    'TRANSPORT':('transporte',),
}


def select_series(role, data):
    """Preserva alcance y ausencia; no transforma faltantes en cero."""
    allowed=SERVICES.get(role,())
    result=[]
    for owner,title in SERIES:
        if role=='TRANSPORT' and owner!='transporte':continue
        if owner not in allowed:
            result.append((owner,title,None,'No disponible para este perfil.'));continue
        payload=data.get(owner)
        if payload is None:
            result.append((owner,title,None,'Información temporalmente no disponible.'));continue
        matches=[entry for entry in payload['series'] if entry['title']==title]
        if len(matches)!=1:
            result.append((owner,title,None,'Indicador no disponible.'));continue
        result.append((owner,title,{'scope':payload['scope'],'from_at':payload['from_at'],
                                  'until_at':payload['until_at'],'updated_at':payload['updated_at'],
                                  'unit':'registros','values':[],
                                  **matches[0]},None))
    return result


class BarChart(QWidget):
    """Barras suplementarias; la tabla adyacente conserva los valores exactos."""
    def __init__(self,values, parent=None):
        super().__init__(parent)
        self.values=[(v['label'],float(v['value'])) for v in values if v['value'] is not None]
        self.setMinimumHeight(max(60,len(self.values)*30+16))
        self.setAccessibleName('Gráfica de barras; valores exactos en la tabla siguiente')

    def paintEvent(self,event):
        painter=QPainter(self);painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(),QColor('#f1f4f6'))
        maximum=max((value for _,value in self.values),default=0)
        left=min(150,max(70,self.width()//3)); area=max(1,self.width()-left-70)
        for index,(text,value) in enumerate(self.values):
            y=8+index*30
            painter.setPen(QColor('#172635'))
            painter.drawText(8,y,left-16,20,Qt.AlignVCenter,painter.fontMetrics().elidedText(str(text),Qt.ElideRight,left-20))
            if maximum:
                painter.setPen(Qt.NoPen);painter.setBrush(QColor('#a31731'))
                painter.drawRoundedRect(left,y,round(area*value/maximum),20,3,3)
            painter.setPen(QColor('#172635'));painter.drawText(left+area+5,y,60,20,Qt.AlignVCenter,f'{value:g}')
        painter.end()


def period_dialog(window):
    dialog=QDialog(window);dialog.setWindowTitle('Periodo de indicadores');dialog.resize(600,230)
    form=QFormLayout(dialog);form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
    end=QDateTimeEdit(QDateTime.currentDateTime());start=QDateTimeEdit(end.dateTime().addDays(-30))
    for widget in (start,end):widget.setCalendarPopup(True);widget.setDisplayFormat('dd/MM/yyyy HH:mm')
    form.addRow('Desde · hora local',start);form.addRow('Hasta · hora local',end)
    note=QLabel('Periodo de hasta 366 días. El final no está incluido.');note.setWordWrap(True);form.addRow(note)
    message=QLabel('');message.setWordWrap(True);form.addRow(message)
    row=QHBoxLayout();submit=QPushButton('Consultar indicadores');submit.setObjectName('primary');cancel=QPushButton('Cancelar')
    row.addWidget(submit);row.addWidget(cancel);form.addRow(row)
    def accept():
        a,b=start.dateTime(),end.dateTime()
        if a>=b or a.secsTo(b)>366*86400:message.setText('Elige un periodo válido de hasta 366 días.');return
        dialog.accept()
    submit.clicked.connect(accept);cancel.clicked.connect(dialog.reject)
    if dialog.exec()!=QDialog.Accepted:return None
    return {'from_at':start.dateTime().toUTC().toString(Qt.ISODate),'until_at':end.dateTime().toUTC().toString(Qt.ISODate)}


def show_dashboard(window,role,data,label):
    dialog=QDialog(window);dialog.setWindowTitle('Indicadores operativos');dialog.resize(800,680)
    outer=QVBoxLayout(dialog);note=QLabel('Indicadores autorizados por servicio. No representan decisiones clínicas.')
    note.setWordWrap(True);outer.addWidget(note)
    scroll=QScrollArea();scroll.setWidgetResizable(True);content=QWidget();layout=QVBoxLayout(content)
    for owner,title,series,error in select_series(role,data):
        heading=QLabel(title);heading.setObjectName('title');layout.addWidget(heading)
        if error:layout.addWidget(QLabel(error));continue
        scope=QLabel(f"{series['scope']} · {series['population']} · Base: {series['denominator']} · {series['unit']}")
        scope.setWordWrap(True);layout.addWidget(scope)
        def local_time(value):
            parsed=QDateTime.fromString(value,Qt.ISODate)
            return parsed.toLocalTime().toString('dd/MM/yyyy HH:mm') if parsed.isValid() else 'No disponible'
        period=QLabel(f"Desde {local_time(series['from_at'])} · hasta {local_time(series['until_at'])} (exclusivo) · actualizado {local_time(series['updated_at'])} · hora local")
        period.setWordWrap(True);layout.addWidget(period)
        values=series['values']
        if not values or all(v['value'] is None for v in values):layout.addWidget(QLabel('Sin datos para el periodo.'));continue
        if title=='Recolección a aceptación' and len(values)==1:
            number=values[0]['value']
            if number is not None:
                average=QLabel(f'{number:g} {series["unit"]}');average.setObjectName('title');layout.addWidget(average)
        elif all(v['value'] is None or v['value']>=0 for v in values):
            layout.addWidget(BarChart([{'label':label(str(v['label'])),'value':v['value']} for v in values]))
        else:layout.addWidget(QLabel('Consulta los valores en la tabla.'))
        table=QTableWidget(len(values),2);table.setHorizontalHeaderLabels(['Categoría','Valor']);table.verticalHeader().hide()
        table.setEditTriggers(QTableWidget.NoEditTriggers);table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setMinimumHeight(min(320,65+len(values)*32));table.setMaximumHeight(min(320,65+len(values)*32))
        for index,value in enumerate(values):
            table.setItem(index,0,QTableWidgetItem(label(str(value['label']))))
            number=value['value'];table.setItem(index,1,QTableWidgetItem('Sin datos' if number is None else f'{number:g}'))
        layout.addWidget(table)
    layout.addStretch();scroll.setWidget(content);outer.addWidget(scroll,1)
    close=QPushButton('Cerrar');close.clicked.connect(dialog.accept);outer.addWidget(close);dialog.exec()


def open_analytics(window,label):
    if not window.client or not window.client.user:return
    binding=OperationContext(window);role=binding.actor[2]
    if role not in SERVICES:window.status.setText('Los indicadores no están disponibles para este perfil.');return
    params=period_dialog(window)
    if not params:return
    if not binding.current():window.status.setText('La sesión cambió. Vuelve a consultar.');return
    def fetch():
        result={}
        for service in SERVICES[role]:
            binding.check()
            try:result[service]=binding.client.authorized(service,'/api/v1/portal-metrics','portal_metrics',params=params)
            except ApiError as exc:
                if exc.status==401:raise
                result[service]=None
            except (ConnectionError,ContractError):result[service]=None
        return result
    window.run_in_context(binding,fetch,lambda data:show_dashboard(window,role,data,label),'Consultando indicadores…')
