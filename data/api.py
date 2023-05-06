import flask
from .films import Films
from . import db_session
from flask import jsonify, request

blueprint = flask.Blueprint(
    'news_api',
    __name__,
    template_folder='templates'
)



@blueprint.route('/api/news')
def get_news():
    db_sess = db_session.create_session()
    news = db_sess.query(Films).all()
    return jsonify(
        {
            'films':
                [item.to_dict(only=('team_leader', 'film', 'user.name')) 
                 for item in news]
        }
    )

@blueprint.route('/api/news/<int:film_id>', methods=['GET'])
def get_one_news(film_id):
    db_sess = db_session.create_session()
    films = db_sess.query(Films).get(film_id)
    if not films:
        return jsonify({'error': 'Not found'})
    return jsonify(
        {
            'film': films.to_dict(only=(
                'team_leader', 'film', 'user.name'))
        }
    )

@blueprint.route('/api/films', methods=['POST'])
def create_news():
    if not request.json:
        return jsonify({'error': 'Empty request'})
    elif not all(key in request.json for key in
                 ['id', 'team_leader', 'film', 'work_size', 'collaborators', 'start_date', 'end_date', 'is_finished']):
        return jsonify({'error': 'Bad request'})
    db_sess = db_session.create_session()
    films = Films(
        id = request.json['id'],
        team_leader = request.json['team_leader'],
        film = request.json['film'],
        work_size = request.json['work_size'],
        collaborators = request.json['collaborators'],
        start_date = request.json['start_date'],
        end_date = request.json['end_date'],
        is_finished = request.json['is_finished']
    )
    db_sess.add(films)
    db_sess.commit()
    return jsonify({'success': 'OK'})

@blueprint.route('/api/news/<int:films_id>', methods=['DELETE'])
def delete_news(films_id):
    db_sess = db_session.create_session()
    films = db_sess.query(Films).get(films_id)
    if not films:
        return jsonify({'error': 'Not found'})
    db_sess.delete(films)
    db_sess.commit()
    return jsonify({'success': 'OK'})