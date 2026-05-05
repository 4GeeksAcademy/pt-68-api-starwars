"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planets
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)


# /////////////////////////////////////////////////////////////////////// trae todos los registros de usuarios
@app.route('/user', methods=['GET'])
def handle_hello():

    try:
        # consultar a la base de datos los registros de usuarios
        query_results= User.query.all()

        # validar si la lista esta vacia
        if not query_results:
            return jsonify({"msg": "Usuarios no encontrados"}), 400 

        # aplico map para usar serialize()
        results= list(map(lambda item: item.serialize(), query_results))


        response_body = {
            "msg": "lista de usuarios encontrada",
            "results": results
        }

        return jsonify(response_body), 200
           
    except Exception as error:
         #en caso de error se captura la excepcion
        print(f"Error al obtener los ususarios: {error}")
        return jsonify({"msg": "Internal Server Error", "error": str(error)}), 500




# ///////////////////////////////////////////////////////////////////////// Muestra la información de un solo planeta según su id


@app.route('/planet/<int:planet_id>', methods=['GET'])
def planet_by_id(planet_id):

    try:
        # consultar en la tabla planets el primer registro que coincid con el id 
        query_results= Planets.query.filter_by(id=planet_id).first()

        # validar si existe el planeta
        if not query_results:
            return jsonify({"msg": "Planeta no encontrado "}), 400 

        response_body = {
            "msg": "planeta encontrado",
            "results": query_results.serialize()
        }

        return jsonify(response_body), 200
           
    except Exception as error:
         #en caso de error se captura la excepcion
        print(f"Error al obtener el planeta por id: {error}")
        return jsonify({"msg": "Internal Server Error", "error": str(error)}), 500


#////////////////////////////////////////////////////////////////////////////// crea la información de un usuario nuevo


@app.route('/user', methods=['POST'])
def create_user():
    # siempre en formato JSON
    data= request.get_json()

    #verificando que el mensaje no este vacio
    if not data:
        return jsonify({"msg": "no se proporcionaron datos"}), 400

    #extraer los valores de los campos 
    email= data.get("email")
    password= data.get("password")
    is_active= data.get("is_active", False)

    #validar si el email esta registrado
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"msg": "ya existe un usuario registrado con ese email"}), 409
    
    #crea un registro nuevo 
    new_user= User(
        email= email,
        password= password,
        is_active= is_active
    )

    #debe ser guardada en la base de datos
    db.session.add(new_user)

    try:
        #confirmar los cambios de forma permanente
        db.session.commit()
        return jsonify(new_user.serialize()), 201
    
    except Exception as error:
         #en caso de error se captura la excepcion
        print(f"Error al crear usuario: {error}")
        return jsonify({"msg": "Internal Server Error", "error": str(error)}), 500


#////////////////////////////////////////////////////////////////////////////
# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
