# coding: utf-8

from django import forms
from django.utils.safestring import mark_safe 

class DayWidget(forms.Widget):
	class Media:
		css = {'all': ('zebra-datepicker/css/default.css',)}
		js = ('zebra-datepicker/js/zebra_datepicker.js',)

	def render(self, name, value, attrs):
		template = u'''
<input type="text" name="%(name)s" value="%(value)s" id="id_%(name)s" />
<script>
$("#id_%(name)s").Zebra_DatePicker({
	format: 'Y-m-d',
	onSelect: function(a,b,c,e){e.keyup()},
	onClear: function(e){e.keyup()}
});
</script>
'''
		return mark_safe(template % {'name': name, 'value': value if value else ''})
		
class MonthWidget(forms.Widget):
	class Media:
		css = {'all': ('zebra-datepicker/css/default.css',)}
		js = ('zebra-datepicker/js/zebra_datepicker.js',)

	def render(self, name, value, attrs):
		template = u'''
<input type="text" name="%(name)s" value="%(value)s" id="id_%(name)s" />
<script>
$("#id_%(name)s").Zebra_DatePicker({
	format: 'Y-m',
	onSelect: function(a,b,c,e){e.keyup()},
	onClear: function(e){e.keyup()}
});
</script>
'''
		return mark_safe(template % {'name': name, 'value': value if value else ''})

class YearWidget(forms.Widget):
	class Media:
		css = {'all': ('zebra-datepicker/css/default.css',)}
		js = ('zebra-datepicker/js/zebra_datepicker.js',)

	def render(self, name, value, attrs):
		template = u'''
<input type="text" name="%(name)s" value="%(value)s" id="id_%(name)s" />
<script>
$("#id_%(name)s").Zebra_DatePicker({
	format: 'Y',
	onSelect: function(a,b,c,e){e.keyup()},
	onClear: function(e){e.keyup()}
});
</script>
'''
		return mark_safe(template % {'name': name, 'value': value if value else ''})

class JSONEditorWidget(forms.Textarea):
	class Media:
		css = {'all': ('jsoneditor/jsoneditor.css',)}
		js = ('jsoneditor/jsoneditor.js',) 

	def render(self, name, value, attrs):
		template = u'''
<div style="display:none">
	<textarea id="id_%(name)s" name="%(name)s">%(value)s</textarea>
</div> 
<div id="id_%(name)s_editor">
</div>
<script>
	var %(safe_name)s_editor = new jsoneditor.JSONEditor	(
							document.getElementById("id_%(name)s_editor"),
							{
								change:	
									function() {
										document.getElementById("id_%(name)s").innerHTML = JSON.stringify(%(safe_name)s_editor.get());
									}
							}, 
							%(value)s
						);
</script>
'''
		return mark_safe(template % {'name': name, 'safe_name': name.replace('-', '_'), 'value': value if value else '{}'})

class CodeMirrorSQLWidget(forms.Textarea):
        class Media:
                css = {'all': ('codemirror/codemirror.css',)}
                js = ('codemirror/codemirror.js', 'codemirror/mode/sql/sql.js',)

        def render(self, name, value, attrs):
                template = u'''
<div><textarea id="id_%(name)s" name="%(name)s">%(value)s</textarea></div>
<script>
        var %(safe_name)s_CodeMirror = CodeMirror.fromTextArea(document.getElementById("id_%(name)s"), {mode: "text/x-plsql", lineNumbers: true, lineWrapping: true});
</script>
'''

                return mark_safe(template % {'name': name, 'safe_name': name.replace('-', '_'), 'value': value if value else ''})

class CodeMirrorPythonWidget(forms.Textarea):
        class Media:
                css = {'all': ('codemirror/codemirror.css',)}
                js = ('codemirror/codemirror.js', 'codemirror/mode/python/python.js',)

        def render(self, name, value, attrs):
                template = u'''
<div><textarea id="id_%(name)s" name="%(name)s">%(value)s</textarea></div>
<script>
        var %(safe_name)s_CodeMirror = CodeMirror.fromTextArea(document.getElementById("id_%(name)s"), {mode: "text/x-python", lineNumbers: true, lineWrapping: true});
</script>
'''

                return mark_safe(template % {'name': name, 'safe_name': name.replace('-', '_'), 'value': value if value else ''})

class CodeMirrorHTMLWidget(forms.Textarea):
        class Media:
                css = {'all': ('codemirror/codemirror.css',)}
                js = ('codemirror/codemirror.js', 'codemirror/mode/xml/xml.js',)

        def render(self, name, value, attrs):
                template = u'''
<div id="div_%(name)s" style="display:none;" class="CodeMirror cm-s-default"></div>
<div id="div_%(name)s_editor"><textarea id="id_%(name)s" name="%(name)s">%(value)s</textarea></div>
<a id="toggle_%(name)s" onclick="javascript:toggle_%(safe_name)s_func()">Preview</a>
<script>
        var %(safe_name)s_CodeMirror = CodeMirror.fromTextArea(document.getElementById("id_%(name)s"), {mode: "text/html", lineWrapping: true});

	function toggle_%(safe_name)s_func() {
		if (document.getElementById("div_%(name)s").style.display == "none") {
			document.getElementById("div_%(name)s").innerHTML = %(safe_name)s_CodeMirror.getValue();
			document.getElementById("div_%(name)s").style.display = "block";
			document.getElementById("div_%(name)s_editor").style.display = "none";
			document.getElementById("toggle_%(name)s").innerHTML = "Edit";
		} else {
			document.getElementById("div_%(name)s").style.display = "none";
			document.getElementById("div_%(name)s_editor").style.display = "block";
			document.getElementById("toggle_%(name)s").innerHTML = "Preview";
		}
	}
</script>
'''

                return mark_safe(template % {'name': name, 'safe_name': name.replace('-', '_'), 'value': value if value else ''})
