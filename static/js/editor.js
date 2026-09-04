document.addEventListener('DOMContentLoaded', function () {
  var textarea = document.querySelector('textarea[name="content"]');
  if (!textarea) return;

  var wrapper = document.createElement('div');
  wrapper.className = 'wysiwyg-wrapper';

  var toolbar = document.createElement('div');
  toolbar.className = 'wysiwyg-toolbar';

  var editable = document.createElement('div');
  editable.className = 'wysiwyg-editable';
  editable.contentEditable = 'true';
  editable.innerHTML = textarea.value || '';

  try {
    document.execCommand('defaultParagraphSeparator', false, 'p');
  } catch (e) { /* not supported in all browsers, harmless */ }

  var buttons = [
    { label: '<b>B</b>', title: 'Bold', cmd: 'bold' },
    { label: '<i>I</i>', title: 'Italic', cmd: 'italic' },
    { label: '<u>U</u>', title: 'Underline', cmd: 'underline' },
    { label: 'H2', title: 'Heading 2', cmd: 'formatBlock', arg: 'H2' },
    { label: 'H3', title: 'Heading 3', cmd: 'formatBlock', arg: 'H3' },
    { label: 'P', title: 'Paragraph', cmd: 'formatBlock', arg: 'P' },
    { label: '&bull; List', title: 'Bullet List', cmd: 'insertUnorderedList' },
    { label: '1. List', title: 'Numbered List', cmd: 'insertOrderedList' },
    { label: '&ldquo;Quote', title: 'Blockquote', cmd: 'formatBlock', arg: 'BLOCKQUOTE' },
    { label: 'Link', title: 'Insert Link', cmd: 'link' },
    { label: 'Clear', title: 'Clear Formatting', cmd: 'removeFormat' },
    { label: '&#8630;', title: 'Undo', cmd: 'undo' },
    { label: '&#8631;', title: 'Redo', cmd: 'redo' },
  ];

  buttons.forEach(function (b) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'wysiwyg-btn';
    btn.title = b.title;
    btn.innerHTML = b.label;
    btn.addEventListener('mousedown', function (e) {
      e.preventDefault(); // keep focus/selection in the editable area
      editable.focus();
      if (b.cmd === 'link') {
        var url = window.prompt('Link URL (https://...)');
        if (url) document.execCommand('createLink', false, url);
        return;
      }
      document.execCommand(b.cmd, false, b.arg || null);
      sync();
    });
    toolbar.appendChild(btn);
  });

  function sync() {
    textarea.value = editable.innerHTML;
  }

  editable.addEventListener('input', sync);
  editable.addEventListener('blur', sync);

  var form = textarea.closest('form');
  if (form) {
    form.addEventListener('submit', sync);
  }

  textarea.style.display = 'none';
  textarea.parentNode.insertBefore(wrapper, textarea);
  wrapper.appendChild(toolbar);
  wrapper.appendChild(editable);
  wrapper.appendChild(textarea);

  sync();
});
