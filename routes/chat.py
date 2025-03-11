from flask import Blueprint, request, jsonify
import openai

# make blue print for ai response 
chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat', methods=['POST'])
def chat():
    # try:
    #     if not user_msg:
    #         return jsonify(['error':])
    # except Exception as e:
    pass
