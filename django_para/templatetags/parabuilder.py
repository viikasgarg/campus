from django_para.models import Para, ParaItem
from django import template
from django.core.cache import cache
from django.utils.safestring import mark_safe
register = template.Library()

def build_para(parser, token):
    """
    {% para para_name %}
    """
    try:
        tag_name, para_name, cols = token.split_contents()
    except:
        raise template.TemplateSyntaxError, "%r tag requires exactly one argument" % token.contents.split()[0]
    return ParaObject(para_name,cols)

def build_paraheader(parser, token):
    """
    {% paraheader para_name %}
    """
    try:
        tag_name, para_name = token.split_contents()
    except:
        raise template.TemplateSyntaxError, "%r tag requires exactly one argument" % token.contents.split()[0]
    return ParaheaderObject(para_name)

class ParaheaderObject(template.Node):
    def __init__(self, para_name):
        self.para_name = para_name

    def render(self, context):
        current_path = context['request'].path
        user = context['request'].user
        paraitems = get_items(self.para_name, current_path, user)
        jsfunction_template = '''
                                $("#dialog-modal-%d").dialog({
                                      autoOpen: false,
                                      show: {
                                        effect: "blind",
                                        duration: 1000
                                      },
                                      hide: {
                                        effect: "explode",
                                        duration: 1000
                                      }
                                    });

                                    $("#detail_%d").click(function() {
                                      $( "#dialog-modal-%d" ).dialog( "open" );
                                    });
                                '''
        i = 0
        jsfunctions = ''
        for item in paraitems:
            jsfunctions += jsfunction_template%(i, i, i)
            i += 1

        if len(jsfunctions) <= 0:
            result = jsfunctions
        else:
            result = '''
                        <script type="text/javascript">
                          $(function() {
                            %s
                          });
                        </script>
                        '''%jsfunctions
        return (result)


class ParaObject(template.Node):
    def __init__(self, para_name, cols):
        self.para_name = para_name
        self.cols = int(cols)

    def render(self, context):
        current_path = context['request'].path
        user = context['request'].user
        paraitems = get_items(self.para_name, current_path, user)

        paras = ''
        para_size = 12/self.cols ## 12 is size of twiiter screen size
        para_rows = ''
        i = 0
        j = 0
        for item in paraitems:
            para = ''
            para = '<h2>' +  item.get('title') + '</h2>\n'
            detail = item.get('description')
            if len(detail) > 100:
                detail = detail[:100]
            para += '<p>' + detail + '</p>\n'
            para +=  '<p><button id=detail_{0} class="btn btn-primary" \
                 role="button">View details &raquo;</button></p>'\
                .format(12*j+i)

            para += '<div id="dialog-modal-{0}" title="{1}"> \
                    <p>{2}</p> </div>'.format(12*j+i,item.get('title'),\
                    item.get('description'))
            para = '<div class="col-lg-{0}">'.format(para_size) + para + '</div>'
            paras += para
            i += 1
        if i*para_size >= 12:
            i = 0
            j += 1
            para_rows += '<div class="row">' + paras + "</div>\n"
            paras = ''
        if len(para_rows) > 0:
            return para_rows
        else:
            return '<div class="row">' + paras + "</div>\n"

def build_sub_para(parser, token):
    """
    {% subpara %}
    """
    return SubParaObject()

class SubParaObject(template.Node):
    def __init__(self):
        pass

    def render(self, context):
        current_path = context['request'].path
        user = context['request'].user
        para = False
        for m in Para.objects.filter(base_url__isnull=False):
            if m.base_url and current_path.startswith(m.base_url):
                para = m

        if para:
            context['subpara_items'] = get_items(para.slug, current_path, user)
            context['subpara'] = para
        else:
            context['subpara_items'] = context['subpara'] = None
        return ''

def get_items(para_name, current_path, user):
    """
    If possible, use a cached list of items to avoid continually re-querying
    the database.
    The key contains the para name, whether the user is authenticated, and the current path.
    Disable caching by setting MENU_CACHE_TIME to -1.
    """
    from django.conf import settings
    cache_time = getattr(settings, 'MENU_CACHE_TIME', 1800)
    debug = getattr(settings, 'DEBUG', False)

    if cache_time >= 0 and not debug:
        cache_key = 'django-para-items/%s/%s/%s'  % (para_name, current_path, user.is_authenticated())
        paraitems = cache.get(cache_key, [])
        if paraitems:
            return paraitems
    else:
        paraitems = []

    try:
        para = Para.objects.get(slug=para_name)
    except Para.DoesNotExist:
        return []

    for i in ParaItem.objects.filter(para=para).order_by('order'):
        current = ( i.link_url != '/' and current_path.startswith(i.link_url)) or ( i.link_url == '/' and current_path == '/' )
        if para.base_url and i.link_url == para.base_url and current_path != i.link_url:
            current = False
        show_anonymous = i.anonymous_only and user.is_anonymous()
        show_auth = i.login_required and user.is_authenticated()
        if (not (i.login_required or i.anonymous_only)) or (i.login_required and show_auth) or (i.anonymous_only and show_anonymous):
            paraitems.append({'url': i.link_url, 'title': i.title, 'current': current,  'description': i.description,})

    if cache_time >= 0 and not debug:
        cache.set(cache_key, paraitems, cache_time)
    return paraitems

register.tag('para', build_para)
register.tag('paraheader', build_paraheader)
register.tag('subpara', build_sub_para)
