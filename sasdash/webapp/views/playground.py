import os
import glob
import uuid

from flask import Blueprint
from flask import render_template, redirect, url_for

from ..forms import LayoutConfigCheckbox, LocalFilePattern

playground = Blueprint(
    'playground',
    __name__,
    url_prefix='/playground',
)


@playground.route('/')
def playground_index():
    return render_template('playground.html')


@playground.route('/1d_profile', defaults={'UUID': None})
@playground.route('/1d_profile/<string:UUID>', methods=('GET', 'POST'))
def profile_analysis(UUID=None):
    if UUID is None:
        new_dirname = uuid.uuid4().hex
        return redirect(url_for('playground.profile_analysis', UUID=new_dirname))
    else:
        # TODO: check exist
        pass
    filepattern_input = LocalFilePattern()
    layouts_checkbox = LayoutConfigCheckbox({})

    if filepattern_input.validate_on_submit():
        p = filepattern_input.filepattern.data
        files = sorted(glob.glob(p))
    else:
        files = []
    files = [os.path.split(f)[-1] for f in files]
    return render_template(
        '1d_profile.html',
        filepattern_input=filepattern_input,
        files=enumerate(files),
        layouts_checkbox=layouts_checkbox,
    )


@playground.route('/2d_image', defaults={'UUID': None})
@playground.route('/2d_image/<string:UUID>')
def image_analysis(UUID=None):
    if UUID is None:
        new_dirname = uuid.uuid4().hex
        return redirect(url_for('playground.image_analysis', UUID=new_dirname))
    else:
        # TODO: check exist
        pass
    return """Hello, here is 2D image analysis.
    Roadmap: Upload scattering images. Calculate radial profile or else analysis.
    """


@playground.route('/3d_density', defaults={'UUID': None})
@playground.route('/3d_density/<string:UUID>')
def density_analysis(UUID=None):
    if UUID is None:
        new_dirname = uuid.uuid4().hex
        return redirect(url_for('playground.density_analysis', UUID=new_dirname))
    else:
        # TODO: check exist
        pass
    return """Hello, here is 3D Density analysis.
    Roadmap: Upload density file or fetch model from PDB database.
    Display in browser. Calculate 1D profile from model. More...
    """
