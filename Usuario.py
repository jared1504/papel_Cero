from distutils import extension
import re
from flask_mysqldb import MySQL
from flask import Flask, session
import os
import bcrypt
import uuid
app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'papel_cero'
mysql = MySQL(app)

class Usuario:
    
    def validarLogin():
        mensajes=[]
        if not Usuario.password or not Usuario.email:
            mensajes.append('Debe ingresar los datos de acceso')
        elif not Usuario.email:
            mensajes.append('Debe ingresar el Correo Electrónico')
        elif not Usuario.password :
            mensajes.append('Debe ingresar su Contraseña')

        cur = mysql.connection.cursor()
        consulta = cur.execute("SELECT hash FROM usuarios WHERE email='"+Usuario.email+"' LIMIT 1")
        if not consulta:  # El usuario no Existe
            mensajes.append('No existe el usuario')
        else:
            hash = cur.fetchone()[0]
            byteHash = hash.encode('utf-8')
            bytePwd = Usuario.password.encode('utf-8')
            # verifica que el password sea valido
            valido = bcrypt.checkpw(bytePwd, byteHash)
            if not valido:  # password incorrecto
                mensajes.append('Contraseña Incorrecta')

        return mensajes

    def obtenerLogin():
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, nombre, admin FROM usuarios WHERE email='"+Usuario.email+"' LIMIT 1")
        return cur.fetchone()

    def miPerfil():
        cur = mysql.connection.cursor()
        consulta = "SELECT nombre, aPaterno, aMaterno, CURP, email FROM usuarios WHERE id= '" + str(session['id']) + "' LIMIT 1"
        cur.execute(consulta)
        return cur.fetchone()

    def all():
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, nombre, aPaterno, aMaterno FROM usuarios WHERE admin = 0")
        users = cur.fetchall()
        return users

    def validarUsuario():
        expresion_regular = r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"
        expresion_curp=   r"(^[A-Z]{1}[AEIOU]{1}[A-Z]{2}[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|1[0-9]|2[0-9]|3[0-1])[HM]{1}(AS|BC|BS|CC|CS|CH|CL|CM|DF|DG|GT|GR|HG|JC|MC|MN|MS|NT|NL|OC|PL|QT|QR|SP|SL|SR|TC|TS|TL|VZ|YN|ZS|NE)[B-DF-HJ-NP-TV-Z]{3}[0-9A-Z]{1}[0-9]{1}$)"    
        mensajes = []
        if not Usuario.nombre:##comprobar que los datos existan y sean validos
            mensajes.append('El nombre es Obligatorio')
        elif not Usuario.aPaterno:
            mensajes.append('El apellido paterno es Obligatorio')
        elif not Usuario.aMaterno:
            mensajes.append('El apellido materno es Obligatorio')
        elif not Usuario.CURP:
            mensajes.append('La CURP es Obligatoria')
        elif not Usuario.correo:
            mensajes.append('Debes agregar una Correo Electrónico')
        elif not Usuario.correo:
            mensajes.append('Debe ingresar un Correo Electrónico')
        elif not (re.match(expresion_regular, Usuario.correo) is not None):
            mensajes.append('Correo Electrónico no válido')
        elif not (re.match(expresion_curp, Usuario.CURP) is not None):
            mensajes.append('CURP no válida')
        elif not Usuario.password:
            mensajes.append('Debes agregar una contraseña')
        elif Usuario.password != Usuario.confirma:
            mensajes.append('Las contraseñas no coinciden')
        elif not Usuario.publicKey:
            mensajes.append('Debes adjuntar el archivo de la Llave Pública')
        if mensajes==[]:
            cur = mysql.connection.cursor()
            existeCorreo = cur.execute("SELECT id FROM usuarios WHERE email = '"+Usuario.correo+"' LIMIT 1")
            if existeCorreo:
                # El correo ya esta ocupado
                mensajes.append('El Correo Electrónico ya es usado por otra Persona')
            else:
                existeCURP = cur.execute("SELECT id FROM usuarios WHERE CURP = '"+Usuario.CURP+"' LIMIT 1")
                if existeCURP:
                    # La curp ya esta ocupada
                    mensajes.append('La CURP ya fue registrada por otra Persona')
        return mensajes

    def crearUsuario():
        bytePwd = Usuario.password.encode('utf-8')
        mySalt = bcrypt.gensalt()
        hash = bcrypt.hashpw(bytePwd, mySalt)##hasear password
        nombre_unico = str(uuid.uuid4())##crear un nombre unico para la llave publica
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO usuarios (nombre, aPaterno, aMaterno, CURP, publicKey, email, hash) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                    (Usuario.nombre, Usuario.aPaterno, Usuario.aMaterno, Usuario.CURP, nombre_unico, Usuario.correo, hash))
        mysql.connection.commit()
        Usuario.publicKey.save(os.path.join("publicKeys/"+nombre_unico+".pam"))##guardar Archivo con nombre unico

    def validarActualiza():
        expresion_regular = r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"
        mensajes=[]
        if not Usuario.correo:
            mensajes.append('Debe ingresar un Correo Electrónico')
        elif not (re.match(expresion_regular, Usuario.correo) is not None):
            mensajes.append('Correo Electrónico no válido')
        return mensajes

    def verificaCorreo():
        cur = mysql.connection.cursor()
        existe = cur.execute("SELECT id FROM usuarios WHERE email = '"+Usuario.correo+"' LIMIT 1")
        id=cur.fetchone()[0]
        return id, existe
    
    def actualizaUsuario():
        cur = mysql.connection.cursor()
        cur.execute("UPDATE usuarios SET email= '" + Usuario.correo+"' WHERE id = "+str(session['id']))
        mysql.connection.commit()

    def all():
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, nombre, aPaterno, aMaterno, CURP, email FROM usuarios WHERE admin =0")
        return cur.fetchall()

    def publicKey():
        cur = mysql.connection.cursor()
        cur.execute("SELECT publicKey FROM usuarios WHERE id='"+str(session['id'])+"'")
        return cur.fetchone()[0]


    def obtenerUsuario(id):
        cur = mysql.connection.cursor()
        consulta = "SELECT nombre, aPaterno, aMaterno, CURP, email FROM usuarios WHERE id= '" + str(id) + "' LIMIT 1"
        cur.execute(consulta)
        return cur.fetchone()