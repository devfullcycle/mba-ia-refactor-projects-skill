from flask import jsonify
from database import get_db
from config.settings import Config

def health_check():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT 1")
        
        cursor.execute("SELECT COUNT(*) FROM produtos")
        produtos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        usuarios = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        pedidos = cursor.fetchone()[0]

        return jsonify({
            "status": "ok",
            "database": "connected",
            "counts": {
                "produtos": produtos,
                "usuarios": usuarios,
                "pedidos": pedidos
            },
            "versao": "1.0.0",
            "ambiente": "producao",
            "db_path": Config.DB_PATH,
            "debug": Config.DEBUG,
            "secret_key": "********"
        }), 200
    except Exception as e:
        return jsonify({"status": "erro", "detalhes": str(e)}), 500
