from datetime import datetime
from flask_mysqldb import MySQL
from flask import Flask, session
import os
import uuid
from datetime import datetime
app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'papel_cero'
mysql = MySQL(app)
class Documento:
    
    def validarDocumento():
        mensajes = []
        if not Documento.titulo:
            mensajes.append('Debe ingresar un Titulo')
        if not Documento.descripcion:
            mensajes.append('Debe ingresar una Descripcion')
        if not Documento.archivo:
            mensajes.append('Debe adjuntar un archivo')
        if Documento.usuarios == "0":
            mensajes.append('Debe seleccionar un usuario')
        return mensajes

    def crearDocumento():
        nombre_unico = str(uuid.uuid4())
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO documentos (titulo,descripcion,nombreArchivo,fechaCreacion) VALUES (%s,%s,%s,%s)',
                    (Documento.titulo, Documento.descripcion, nombre_unico, datetime.today()))
        mysql.connection.commit()
        idDocumento = cur.lastrowid
        
        cur.execute('INSERT INTO usuarios_documentos (idUsuario,idDocumento) VALUES (%s,%s)',
                    (Documento.usuarios, idDocumento))
        mysql.connection.commit()
        Documento.archivo.save(os.path.join("Archivos/"+ nombre_unico+".pdf"))
        
    def where(estado):
        cur = mysql.connection.cursor()
        consulta = "SELECT d.* FROM usuarios_documentos as ud, documentos as d"
        consulta += " WHERE '" + str(session['id']) + "' = ud.idUsuario AND ud.idDocumento = d.id AND ud.estado="+estado
        cur.execute(consulta)
        docs = cur.fetchall()
        return docs

    def all(estado):
        cur = mysql.connection.cursor()
        sql="SELECT d.* FROM documentos as d, usuarios_documentos as ud WHERE ud.idDocumento=d.id AND ud.estado = "+str(estado)
        print(sql)
        cur.execute(sql)
        return cur.fetchall()
    
    def detalleDocumento(id):
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM documentos WHERE id='"+id+"' LIMIT 1")
        doc = cur.fetchone()
        cur.execute("SELECT u.id,u.nombre,u.aPaterno,u.aMaterno FROM usuarios as u, usuarios_documentos as ud "
                    + "WHERE u.id = ud.idUsuario AND ud.idDocumento ='"+id+"'")
        users = cur.fetchall()

        return doc, users
    
    def validarFirma():
        mensajes = []
        if not Documento.llave:
            mensajes.append('Debe adjuntar su llave privada')
        return mensajes

    def documentoFirmado(id):
        cur = mysql.connection.cursor()
        sql="SELECT hash FROM usuarios_documentos WHERE idDocumento ='"+id+"'"
        cur.execute(sql)
        doc = cur.fetchone()[0]
        return doc