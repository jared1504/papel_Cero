from ast import keyword
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import os
import webbrowser
from Usuario import Usuario
from Documento import Documento

from inspect import signature
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
import codecs
import uuid
import fitz
from datetime import datetime

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'papel_cero'
mysql = MySQL(app)


# session
app.secret_key = 'mysecretkey'


@app.route('/')
def login():
    # session.clear() #se borran los mensajes
    return render_template('login.html')


@app.route('/loguear', methods=['POST'])
def loguear():
    if request.method == 'POST':
        Usuario.email = request.form['email']
        Usuario.password = request.form['password']
        mensajes = Usuario.validarLogin()  # validar las credenciales
        if mensajes == []:  # si ingreso las credenciales y son correctas
            id = Usuario.obtenerLogin()

            session['id'] = id[0]
            session['nombre'] = id[1]
            if id[2]:  # se redireciona segun si es admin o no
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('menu'))
        else:  # se retorna al login mostrando los errores
            flash(mensajes)
            return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# rutas usuario


@app.route('/menu')
def menu():
    if not session:
        return redirect(url_for('login'))
    else:
        docs = Documento.where("0")  # 0 para obtener los que aun no se firman
        if docs == ():
            flash("No hay documentos por firmar")
        return render_template('menu/menu.html', documentos=docs)


@app.route('/firmados')
def firmados():
    if not session:
        return redirect(url_for('login'))
    else:
        docs = Documento.where("1")  # 0 para obtener los que ya se firmaron
        if docs == ():
            flash("No hay documentos Firmados")
        return render_template('menu/firmados.html', documentos=docs)


@app.route('/detalle-firmado', methods=['GET'])
def verDocumento():
    id = request.args.get('documento')
    doc, users = Documento.detalleDocumento(id)
    ruta = os.path.join(os.getcwd(), "Archivos\\"+doc[3]+".pdf")
    return render_template('menu/detalle-documento.html', documento=doc, usuarios=users, path=ruta)


@app.route('/detalle-documento', methods=['GET'])
def verDetalleDocumento():
    id = request.args.get('documento')
    doc, users = Documento.detalleDocumento(id)
    ruta = os.path.join(os.getcwd(), "Archivos\\"+doc[3]+".pdf")
    return render_template('menu/ver-detalle-documento.html', documento=doc, usuarios=users, path=ruta)


@app.route('/firmar-documento', methods=['POST'])
def firmarDocumento():
    if request.method == 'POST':
        id = request.form['documento']
        nombre = request.form['nombre']
        Documento.llave = request.files['privKey']
        mensajes = Documento.validarFirma()

        if mensajes == []:
            private_key = Documento.llave.read()
            ruta = os.path.join(os.getcwd()+"\\Archivos\\"+nombre+".pdf")

            # Se obtiene el texto del documento a firmar
            doc = fitz.open(ruta)
            i = 0
            text = ""
            while i < doc.pageCount:
                pagina = doc.loadPage(i)
                text += pagina.getText("text")
                i += 1

            # se agrega el nombre del usuario que firma
            #text+="\nfirma: "+session['nombre']
            #print("antes")
            #print(doc.metadata)

            # se genera el hash con la llave privada y el contenido del documento
            h = SHA256.new(text.encode("utf8"))
            priv_key = RSA.importKey(private_key)
            singer = PKCS1_v1_5.new(priv_key)
            signature = singer.sign(h)
            hexify = codecs.getencoder('hex')
            m = hexify(signature)[0]

            # verificar que la llave privada coincida

            # obtiene la llave publica del usuario
            pKey = Usuario.publicKey()
            public_key = open('publicKeys/'+pKey+'.pam').read()
            pub_key = RSA.importKey(public_key)

            # Se genera un nuevo hash con la firma
            #h2 = SHA256.new(text.encode("utf8"))
            signer = PKCS1_v1_5.new(pub_key)

            # se decodifica el hash
            signature = m.decode("utf8")
            hexify = codecs.getdecoder('hex')
            m2 = hexify(signature)[0]

            # se comprueba si es la llave privada correcta o no
            rsp = 1 if (signer.verify(h, m2)) else 0
            if rsp:  # la llave privada es correcta
                # establecer metadatos de la firma al pdf
                meta = doc.metadata
                firma = str(datetime.now())
                meta["keywords"] += "Firma"+session['nombre']+": "+firma
                doc.set_metadata(meta)
                """
                print("\n\nDespues")
                print(doc.metadata)

                
                #se guarda el nuevo documento con la firma
                docNew = fitz.open()
                pagina = docNew.new_page()
                posicion = fitz.Point(50, 50)
                pagina.insert_text(posicion,text)
                # Guardamos los cambios en el documento
                docNew.write()

                """
                # Guardamos el fichero PDF
                # crear un nombre unico para el hash de la firma
                nombre_unico = str(uuid.uuid4())

                ruta = os.path.join("firmas/"+nombre_unico)
                # guardar el doc del hash
                arch = open(ruta+".pam", "w")
                arch.write(m.decode('utf8'))

                # Guardar el hash en la bd
                cur = mysql.connection.cursor()
                sql="UPDATE usuarios_documentos SET estado='1', hash='" + nombre_unico + "', fechaFirma ='" + str(datetime.today()) + "' WHERE idUsuario = " + str(session['id'])+" AND idDocumento="+id
                cur.execute(sql)
                mysql.connection.commit()

                #ver si todos los usuarios ya firmaron
                sql="SELECT count(*) FROM usuarios_documentos WHERE estado = '0' AND idDocumento="+id
                cur.execute(sql)
                n = cur.fetchone()[0]
                print(n)
                if n==0:
                    sql="UPDATE documentos SET estado='1' WHERE id="+id
                    cur.execute(sql)
                    mysql.connection.commit()

                flash("Documento Firmado Con Éxito")
                return redirect(url_for('menu'))

            else:  # la llave privada es incorrecta
                mensajes.append("La llave privada no coincide con el usuario")
                flash(mensajes)
                return redirect(url_for('verDetalleDocumento', documento=id))


@app.route('/pdf', methods=['GET'])
def pdf():
    nombre = request.args.get('nombre')
    ruta = os.path.join(os.getcwd(), "Archivos/"+nombre+".pdf")
    webbrowser.open_new(ruta)
    return redirect(url_for('menu'))


@app.route('/pdf-firmado', methods=['GET'])
def pdfFirmado():
    id = request.args.get('id')
    doc = Documento.documentoFirmado(id)
    ruta = os.path.join(os.getcwd(), "firmas/"+doc+".pdf")
    webbrowser.open_new(ruta)
    return redirect(url_for('firmados'))


@app.route('/miperfil')
def perfil():
    if not session:
        return redirect(url_for('login'))
    else:
        datos = Usuario.miPerfil()
        return render_template('menu/perfil.html', perfil=datos)


@app.route('/actualizar-perfil', methods=['POST'])
def actualizarPerfil():
    if request.method == 'POST':
        Usuario.correo = request.form['correo']
        mensajes = Usuario.validarActualiza()  # validacion de los inputs
        if mensajes == []:  # comprobar que el correo no es usado por alguien mas
            id, existe = Usuario.verificaCorreo()
            if (existe and id == session['id']) or not existe:
                Usuario.actualizaUsuario()  # se actualiza el correo
                flash('Datos Actualizados con Éxito')
                return redirect(url_for('menu'))
            else:
                mensajes.append(
                    'El Correo Electrónico ya es usado por otra Persona')
                flash(mensajes)
                return redirect(url_for('perfil'))
        else:
            flash(mensajes)
        return redirect(url_for('perfil'))

# Rutas Admin


@app.route('/admin')
def admin():
    if not session:
        return redirect(url_for('login'))
    else:
        return render_template('admin/admin.html')


@app.route('/admin/agregar_documento')
def agregarDocumento():
    if not session:
        return redirect(url_for('login'))
    else:
        users = Usuario.all()  # obtener usuarios que firmen
        return render_template('admin/agregar-documento.html', usuarios=users)


@app.route('/admin/guardar_documento', methods=['POST'])
def guardar_documento():
    if request.method == 'POST':
        Documento.titulo = request.form['titulo']
        Documento.descripcion = request.form['descripcion']
        Documento.archivo = request.files['archivo']
        Documento.usuarios = []
        for p in request.form:
            Documento.usuarios.append(p)
        Documento.usuarios.pop(0)
        Documento.usuarios.pop(0)
        mensajes = Documento.validarDocumento()
        if mensajes == []:
            Documento.crearDocumento()
            flash('Documento Agregado con Éxito')
            return redirect(url_for('admin'))
        else:
            flash(mensajes)
            return redirect(url_for('agregarDocumento'))


@app.route('/admin/ver_documentos')
def verDocumentos():
    if not session:
        return redirect(url_for('login'))
    else:
        docs = Documento.all(0)  # obtener todos los documentos
        return render_template('admin/ver-documentos.html', documentos=docs)


@app.route('/admin/ver_firmados')
def verFrimados():
    if not session:
        return redirect(url_for('login'))
    else:
        docs = Documento.all(1)  # obtener todos los documentos
        return render_template('admin/ver-documentos.html', documentos=docs)


@app.route('/admin/verDetalle', methods=['GET'])
def verDetalle():
    id = request.args.get('documento')

    doc, users = Documento.detalleDocumento(id)
    ruta = os.path.join(os.getcwd(), "Archivos\\"+doc[3]+".pdf")
    return render_template('admin/detalle-documento.html', documento=doc, usuarios=users, path=ruta)


@app.route('/admin/verPDF', methods=['GET'])
def verPDF():
    nombre = request.args.get('nombre')
    ruta = os.path.join(os.getcwd(), "Archivos/"+nombre+".pdf")
    webbrowser.open_new(ruta)
    return redirect(url_for('verDocumentos'))


@app.route('/admin/usuarios')
def verUsuarios():
    if not session:
        return redirect(url_for('login'))
    else:
        users = Usuario.all()  # obtener todos los usuarios
        return render_template('admin/ver-usuarios.html', usuarios=users)


@app.route('/admin/agregar-usuario')
def agregar_Usuario():
    if not session:
        return redirect(url_for('login'))
    else:
        return render_template('admin/agregar-usuario.html')


@app.route('/admin/agregarusuario', methods=['POST'])
def agregarUsuario():
    if not session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        Usuario.nombre = request.form['nombre']
        Usuario.aPaterno = request.form['paterno']
        Usuario.aMaterno = request.form['materno']
        Usuario.CURP = request.form['CURP']
        Usuario.correo = request.form['correo']
        Usuario.password = request.form['password']
        Usuario.confirma = request.form['confirma']
        Usuario.publicKey = request.files['publicKey']
        mensajes = Usuario.validarUsuario()
        if mensajes == []:  # verificar si no hay mensajes de error
            Usuario.crearUsuario()  # Guardar Usuario
            flash('Usuario Registrado con Éxito')
            return redirect(url_for('admin'))
        else:  # mostrar errores que hay
            flash(mensajes)
            return redirect(url_for('agregar_Usuario'))


@app.route('/admin/verUsuario', methods=['GET'])
def verUsuario():
    id = request.args.get('usuario')
    user = Usuario.obtenerUsuario(id)
    return render_template('admin/perfil.html', perfil=user)
    return str(user[1])


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True)
