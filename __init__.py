# -*- coding: utf-8 -*-
"""
    zine.plugins.img_upload
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    A plugin to upload images to a static directory, to link then in
    articles easily.
    :copyright: (c) 2011 by gabriel pettier for more details.
    :license: BSD, see LICENSE for more details.
"""
import os
from os.path import dirname, join
from random import choice
from string import letters

from zine.api import *
from zine.views.admin import render_admin_response
from zine.utils.admin import flash
from zine.utils.http import redirect
from zine.utils import dump_json
from zine.utils.forms import TextField
from zine.config import ConfigurationTransactionError
from zine.privileges import BLOG_ADMIN

TEMPLATES = join(dirname(__file__), 'templates')
SHARED_FILES = join(dirname(__file__), 'shared')

def inject_image_form(req, context):
    """This is called before the admin response is rendered. We add the
    """
    add_script(url_for('img_upload/shared', filename='ajax-upload/ajaxupload.js'))
    add_header_snippet('''
        <script type="text/javascript">
        $(document).ready(function() {
        $(".formbox:first").after('<div id="img_upload">click to upload image</div>');
        new AjaxUpload("img_upload", {
            action: "/_services/json/img_upload/upload",
            responseType: "json",
            onComplete: function(file, response){$('#img_upload').after(response)},
            });
        })
        </script>''');


def add_image_manager_link(req, navigation_bar):
    """Called during the admin navigation bar setup. When the options menu is
    traversed we insert our eric the fish link before the plugins link.
    The outermost is the configuration editor, the next one the plugins
    link and then we add our fish link.
    """
    if not req.user.has_privilege(BLOG_ADMIN):
        return
    for link_id, url, title, children in navigation_bar:
        if link_id == 'options':
            children.insert(-3, ('img_upload', url_for('img_upload/config'),
                                 _('Image upload')))


@require_privilege(BLOG_ADMIN)
def show_image_manager_options(req):
    image_dir = req.args.get('images_directory')
    base_url = req.args.get('base_url')
    if image_dir:
        try:
            req.app.cfg.change_single('img_upload/images_directory', image_dir)
        except ConfigurationTransactionError, e:
            flash(_('The images directory could not be changed.'), 'error')

    if base_url:
        try:
            req.app.cfg.change_single('img_upload/base_url', base_url)
        except ConfigurationTransactionError, e:
            flash(_('The base url could not be changed.'), 'error')

    return render_admin_response('admin/img_uploader.html',
            images_directory=req.app.cfg['img_upload/images_directory'],
            base_url=req.app.cfg['img_upload/base_url'])

@require_privilege(BLOG_ADMIN)
def upload_image(req):
    """
    """
    image = req.files['userfile']
    if "image" in image.content_type:
        name = image.filename
        while name in os.listdir(req.app.cfg['img_upload/images_directory']):
            name = '.'.join(name.split('.')[:-1]) + choice(letters) + '.' + name.split('.')[-1]

        image.save(os.path.join(req.app.cfg['img_upload/images_directory'], name))

        return '&lt;img src="'+req.app.cfg['img_upload/base_url']+'/'+name+'"&gt;&lt;/img&gt;<br />'


def setup(app, plugin):
    """This function is called by Zine in the application initialization
    phase. Here we connect to the events and register our template paths,
    url rules, views etc.
    """
    app.connect_event('before-admin-response-rendered', inject_image_form)
    app.connect_event('modify-admin-navigation-bar', add_image_manager_link)

    app.add_config_var('img_upload/images_directory', TextField(default=''))
    app.add_config_var('img_upload/base_url', TextField(default=''))
    app.add_servicepoint('img_upload/upload', upload_image)

    app.add_url_rule('/options/img_upload', prefix='admin',
                     endpoint='img_upload/config',
                     view=show_image_manager_options)

    # add our templates to the searchpath so that Zine can find the
    # admin panel template for the fish config panel.
    app.add_template_searchpath(TEMPLATES)
    app.add_shared_exports('img_upload', SHARED_FILES)