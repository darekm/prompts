/* ******************** file upload  *************************** */

function supportPrinting() {
  //http://stackoverflow.com/questions/1234008/detecting-browser-print-event
  var beforePrint = function () {
    console.log('Functionality to run before printing.');
  };
  var afterPrint = function () {
    console.log('Functionality to run after printing');
  };

  if (window.matchMedia) {
    var mediaQueryList = window.matchMedia('print');
    mediaQueryList.addListener(function (mql) {
      if (mql.matches) {
        beforePrint();
      } else {
        afterPrint();
      }
    });
  }

  window.onbeforeprint = beforePrint;
  window.onafterprint = afterPrint;
  console.log('setup printing');

}

function supportAjaxUploadWithProgress() {
  return supportFileAPI() && supportAjaxUploadProgressEvents() && supportFormData();

  // Is the File API supported?
  function supportFileAPI() {
    var fi = document.createElement('INPUT');
    fi.type = 'file';
    return 'files' in fi;
  };
  // Are progress events supported?
  function supportAjaxUploadProgressEvents() {
    var xhr = new XMLHttpRequest();
    return !!(xhr && ('upload' in xhr) && ('onprogress' in xhr.upload));
  };
  // Is FormData supported?
  function supportFormData() {
    return !!window.FormData;
  }
}


function initFormUpload() {
  var form = document.getElementById('form-id');
  form.onsubmit = function () {
    // FormData receives the whole form
    var formData = new FormData(form);

    // We send the data where the form wanted
    var action = form.getAttribute('action');

    // Code common to both variants
    sendXHRequest(formData, action);

    // Avoid normal form submission
    return false;
  }
}




function onloadstartHandler(evt) {
  try {
    var div = document.getElementById('upload-status');
    div.innerHTML = 'Upload started!';
  }
  catch (Exception) {
    LOG(' Upload start ');
  }
}

// Handle the end of the transmission
function onloadHandler(evt) {
  try {
    var div = document.getElementById('upload-status');
    div.innerHTML = 'Upload successful!';
  }
  catch (Exception) {
    LOG(' Upload successful! ');
  }

}

// Handle the progress
function onprogressHandler(evt) {
  try {
    var div = document.getElementById('progress');
    var percent = Math.round(evt.loaded / evt.total * 100);
    div.innerHTML = 'Progress: ' + percent + '%';
  }
  catch (Exception) {
    LOG(' Progress: ', evt.loaded);
  }

}

function ieReadFile(filename) {
  try {
    var fso = new ActiveXObject("Scripting.FileSystemObject");
    var fh = fso.OpenTextFile(filename, 1);
    var contents = fh.ReadAll();
    fh.Close();
    return contents;
  }
  catch (Exception) {
    return "Cannot open file :(";
  }
}


function handleFiles(aurl, files) {
  var ie, xl;
  try {
    xl = files.length;

  } catch (Exception) { xl = -1; }
  if (xl < 0) {
    sendXMLIE(ieReadFile(this.value), aurl, this.value);

  } else {
    for (var i = 0; i < files.length; i++) {
      var file = files[i];
      fileUploadNew(aurl, file);
    }
  }
}
function fileUpload(aurl, file) {
  // Please report improvements to: marco.buratto at tiscali.it

  var fileName = file.name;
  var fileSize = file.size;
  var fileData = file.getAsBinary(); // works on TEXT data ONLY.

  var boundary = "xxxxxxxxx";

  var xhr = new XMLHttpRequest();

  xhr.open("POST", aurl + '?procedura=F;komenda=3;field=' + escape(fileName), true);
  xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded"); // simulate a file MIME POST request.
  xhr.setRequestHeader("Content-Length", fileSize);

  xhr.onreadystatechange = function () {
    if (xhr.readyState == 4) {
      if ((xhr.status >= 200 && xhr.status <= 200) || xhr.status == 304) {

        if (xhr.responseText == "error") {
          alert(xhr.responseText); // display response.
        }
      }
    }
  }
  /*
    var body = "--" + boundary + "\r\n";
    body += "Content-Disposition: form-data; name='fileId'; filename='" + fileName + "'\r\n";
    body += "Content-Type: application/x-www-form-urlencoded\r\n\r\n";
    body += fileData + "\r\n";
    body += "--" + boundary + "--";
  */
  xhr.sendAsBinary(fileData);
  return true;
}


// Import the Services module for future use, if we're not in
// a browser window where it's already loaded.
//Components.utils.import('resource://gre/modules/Services.jsm');

// Create a constructor for the built-in supports-string class.
//const nsSupportsString = Components.Constructor("@mozilla.org/supports-string;1", "nsISupportsString");
function SupportsString(str) {
  // Create an instance of the supports-string class
  var res = nsSupportsString();

  // Store the JavaScript string that we want to wrap in the new nsISupportsString object
  res.data = str;
  return res;
}

// Create a constructor for the built-in transferable class

//const nsTransferable = Components.Constructor("@mozilla.org/widget/transferable;1", "nsITransferable");

// Create a wrapper to construct an nsITransferable instance and set its source to the given window, when necessary
function Transferable(source) {
  var res = nsTransferable();
  if ('init' in res) {
    // When passed a Window object, find a suitable privacy context for it.
    if (source instanceof Ci.nsIDOMWindow)
      // Note: in Gecko versions >16, you can import the PrivateBrowsingUtils.jsm module
      // and use PrivateBrowsingUtils.privacyContextFromWindow(sourceWindow) instead
      source = source.QueryInterface(Ci.nsIInterfaceRequestor)
        .getInterface(Ci.nsIWebNavigation);

    res.init(source);
  }
  return res;
}


function copyLinkToClipboardFirefox(copyText, sourceWindow) {
  // http://stackoverflow.com/questions/21696052/copy-to-clipboard-with-javascript-in-firefox
  Components.utils.import('resource://gre/modules/Services.jsm');

  // generate the Unicode and HTML versions of the Link
  //    var textUnicode = copyURL;
  //    var textHtml = copyLabel.link(copyURL);
  var textHTML = copyText;

  // add Unicode & HTML flavors to the transferable widget
  var trans = Transferable(sourceWindow);

  //    trans.addDataFlavor("text/unicode");
  //    trans.setTransferData("text/unicode", SupportsString(textUnicode), textUnicode.length * 2); // *2 because it's unicode

  trans.addDataFlavor("text/html");
  trans.setTransferData("text/html", SupportsString(textHtml), textHtml.length * 2); // *2 because it's unicode

  // copy the transferable widget!
  Services.clipboard.setData(trans, null, Services.clipboard.kGlobalClipboard);
  return true;
}

function copyToClip(text) {
  window.prompt("Copy to clipboard: Ctrl+C, Enter", text);
}
function copyToFirefox(atext) {
  //const gClipboardHelper = Components.classes["@mozilla.org/widget/clipboardhelper;1"]
  //                                   .getService(Components.interfaces.nsIClipboardHelper);
  //gClipboardHelper.copyString("Put me on the clipboard, please.");
}

//http://stackoverflow.com/questions/17527870/how-does-trello-access-the-users-clipboard
function copyToClipboardTrelo(atext) {
}

function fallbackCopyTextToClipboard(text) {
  var textArea = document.createElement("textarea");
  textArea.style.position = 'fixed';
  textArea.style.top = 0;
  textArea.style.left = 0;

  // Ensure it has a small width and height. Setting to 1px / 1em
  // doesn't work as this gives a negative w/h on some browsers.
  textArea.style.width = '2em';
  textArea.style.height = '2em';

  // We don't need padding, reducing the size if it does flash render.
  textArea.style.padding = 0;

  // Clean up any borders.
  textArea.style.border = 'none';
  textArea.style.outline = 'none';
  textArea.style.boxShadow = 'none';

  // Avoid flash of white box if rendered for any reason.
  textArea.style.background = 'transparent';
  textArea.value = text;
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();

  try {
    var successful = document.execCommand('copy');
    var msg = successful ? 'successful' : 'unsuccessful';
    console.log('Fallback: Copying text command was ' + msg);
  } catch (err) {
    console.error('Fallback: Oops, unable to copy', err);
  }

  document.body.removeChild(textArea);
}
function copyTextToClipboard(text) {
  if (!navigator.clipboard) {
    fallbackCopyTextToClipboard(text);
    return;
  }
  navigator.clipboard.writeText(text).then(function () {
    console.log('Async: Copying to clipboard was successful!');
  }, function (err) {
    console.error('Async: Could not copy text: ', err);
  });
}

function copyToClipboard(atext) {
  var text = unescape(atext);
  copyTextToClipboard(atext);
}

function copyToClipboardIIR(atext) {
  if (window.clipboardData) {
    window.clipboardData.setData("Text", text);
    return;
  }
  else if (MD.isChrome() && (chrome.extension) && (chrome.extension.sendRequest)) {
    chrome.extension.sendRequest({ type: REQUEST_COPY, content: text });
    return;
  }
  else if ((window.netscape) && (Components)) {
    try {
      try {
        //        copyLinkToClipboardFirefox(text,window);
        copyToClip(text);
      } catch (e) {
        return alert(e.message);
      }

      return;

      //      netscape.security.PrivilegeManager.enablePrivilege('UniversalXPConnect');
      //      var gClipboardHelper = Components.classes['@mozilla.org/widget/clipboardhelper;1']
      //                  .getService(Components.interfaces.nsIClipboardHelper);
      //      gClipboardHelper.copyString(text);
      //      return;
    } catch (e) {
      return alert(e + '\n\nPlease type: "about:config" in your address bar.\nThen filter by "signed".\nChange the value of "signed.applets.codebase_principal_support" to true.\nYou should then be able to use this feature.');
    }
  }
  else
    copyToClip(text);


  //   return alert( "Your browser does not support this feature");
}


function dragenter(e) {
  e.stopPropagation();
  e.preventDefault();
}

function dragover(e) {
  e.stopPropagation();
  e.preventDefault();
}
var
  dropboxurl;

function drop(e) {
  e.stopPropagation();
  e.preventDefault();

  var dt = e.dataTransfer;
  var files = dt.files;


  //  handleFiles(dropboxurl,files);

  for (var i = 0; i < files.length; i++) {
    var file = files[i];

    fileUploadNew(dropboxurl, file);
    var span = document.createElement('tr');
    span.innerHTML = '<td></td><td><p>' + file.name + '</p></td><td></td>';

    document.getElementById('filedropboxfile').insertBefore(span, null);

  }
}



function prepareFileUpload(aUrl) {
  var dropbox;
  dropboxurl = aUrl;
  dropbox = document.getElementById("filedropbox");
  try {
    dropbox.addEventListener("dragenter", dragenter, false);
    dropbox.addEventListener("dragover", dragover, false);
    dropbox.addEventListener("drop", drop, false);
  } catch (ee) { };

  if (supportAjaxUploadWithProgress()) {
    // Ajax uploads are supported!
    // Change the support message and enable the upload button
    var notice = document.getElementById('support-notice');
    //  var uploadBtn = document.getElementById('upload-button-id');
    notice.innerHTML = "";
    //  uploadBtn.removeAttribute('disabled');

    // Init the Ajax form submission
    //  initFullFormAjaxUpload();

    // Init the single-field file upload
    //  initFileOnlyAjaxUpload();
  }


}


function fileUploadIE(aUrl, file) {
  var reader = new FileReader();
  reader.addEventListener("loadend", function () {
    var binary = "";
    var bytes = new Uint8Array(reader.result);
    var length = bytes.byteLength;
    for (var i = 0; i < length; i++) {
      binary += String.fromCharCode(bytes[i]);
    };

    sendXML(binary, aUrl, file.name);
    //            callback(binary);
  });
  reader.readAsArrayBuffer(file);
}

function fileUploadNew(aUrl, file) {
  // Please report improvements to: marco.buratto at tiscali.it

  //  var fileName = file.name;
  //  var fileData = file.getAsBinary(); // works on TEXT data ONLY.

  var reader = new FileReader();
  reader.onload = function (ev) {
    sendXML(this.result, aUrl, file.name);
  }
  try {
    reader.readAsBinaryString(file);
  } catch (err) {
    fileUploadIE(aUrl, file);
  }
  //      reader.readAsArrayBuffer(file);

}

function xhrsendBinary(data, xhr) {

  if (typeof XMLHttpRequest.prototype.sendAsBinary == "function") { // Firefox 3 & 4
    //		var tmp = '';
    //		for (var i = 0; i < data.length; i++) tmp += String.fromCharCode(data.charCodeAt(i) & 0xff);
    //		data = tmp;
    try {
      xhr.setRequestHeader("Content-Length", data.length);
    } catch (Exception) {
      LOG(' dataLength ', data.length);
    }

  }
  else { // Chrome 9
    // http://javascript0.org/wiki/Portable_sendAsBinary

    //                XMLHttpRequest.prototype.sendAsBinary = function(datastr) {
    //                  var ui8a = new Uint8Array(datastr.length);
    //                for (var i = 0; i < datastr.length; i++) {
    //                       ui8a[i] = (datastr.charCodeAt(i) & 0xff);
    //                  }
    //                  this.send(ui8a.buffer);
    //                }

    //             https://gist.github.com/742267
    //		XMLHttpRequest.prototype.sendAsBinary = function(text){
    //			var data = new ArrayBuffer(text.length);
    //			var ui8a = new Uint8Array(data, 0);
    //			for (var i = 0; i < text.length; i++) ui8a[i] = (text.charCodeAt(i) & 0xff);

    //			var bb = new BlobBuilder(); // doesn't exist in Firefox 4
    //			bb.append(data);
    //			var blob = bb.getBlob();
    //			this.send(blob);
    //		}

    XMLHttpRequest.prototype.sendAsBinary = function (datastr) {
      //function byteValue(x) {
      //  return x.charCodeAt(0) & 0xff;
      //}
      //var ords = Array.prototype.map.call(datastr, byteValue);
      //var ui8a = new Uint8Array(ords);
      //this.send(ui8a.buffer);

      var nBytes = datastr.length, ui8Data = new Uint8Array(nBytes);
      for (var nIdx = 0; nIdx < nBytes; nIdx++) {
        ui8Data[nIdx] = datastr.charCodeAt(nIdx) & 0xff;
      }
      this.send(ui8Data.buffer);
    }
  }

  xhr.sendAsBinary(data);
}


function sendXML(aev, aurl, aname) {
  var xhr = getHTTPObject();
  //  new XMLHttpRequest();

  xhr.upload.addEventListener('loadstart', onloadstartHandler, false);
  xhr.upload.addEventListener('progress', onprogressHandler, false);
  xhr.upload.addEventListener('load', onloadHandler, false);


  var fileString = aev;
  var result = document.getElementById("status-notice");

  xhr.open("POST", aurl + '?procedura=F;komenda=3;field=' + escape(aname), true);
  xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded"); // simulate a file MIME POST request.
  //  xhr.setRequestHeader("Content-Length", fileString.length);
  xhr.onreadystatechange = function (evt) {
    if (xhr.status == '200' && evt.target.responseText) {
      var result = document.getElementById("status-notice");
      result.innerHTML = "Finish: <b>" + evt.target.status + "</b>";
    }
    if (xhr.readyState == 4) {
      if ((xhr.status >= 200 && xhr.status <= 200) || xhr.status == 304) {

        if (xhr.responseText == "error") {
          alert(xhr.responseText); // display response.
        }
      }
    }
  }
  //  xhr.sendAsBinary(fileString);
  xhrsendBinary(fileString, xhr);
  return true;
}


function sendXMLIE(aev, aurl, aname) {
  var xhr = getHTTPObject();
  //  new XMLHttpRequest();
  var fileString = aev;
  var result = document.getElementById('status-notice');
  //   result.innerHTML = 'Start upload <pre>' + aname + '</pre>';

  xhr.open("POST", aurl + '?procedura=F;komenda=3;field=' + escape(aname), true);
  xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded"); // simulate a file MIME POST request.
  xhr.setRequestHeader("Content-Length", fileString.length);

  xhr.onreadystatechange = function (evt) {
    if (xhr.status == '200' && evt.target.responseText) {
      var result = document.getElementById('status-notice');
      result.innerHTML = 'Finish: <b>' + evt.target.status + '</b>';
    }
    if (xhr.readyState == 4) {
      if ((xhr.status >= 200 && xhr.status <= 200) || xhr.status == 304) {

        if (xhr.responseText == "error") {
          alert(xhr.responseText); // display response.
        }
      }
    }
  }
  xhr.send(aev);
  return true;
}





function loadjscssfile(filename, filetype) {
  if (filetype == "js") { //if filename is a external JavaScript file
    var fileref = document.createElement('script')
    fileref.setAttribute("type", "text/javascript")
    fileref.setAttribute("src", filename)
  }
  else if (filetype == "css") { //if filename is an external CSS file
    var fileref = document.createElement("link")
    fileref.setAttribute("rel", "stylesheet")
    fileref.setAttribute("type", "text/css")
    fileref.setAttribute("href", filename)
  }
  if (typeof fileref !== "undefined") {
    var head = document.head || document.getElementsByTagName("head");
    head.appendChild(fileref);
  }
}

var filesadded = "" //list of files already added

function checkloadjscssfile(filename, filetype, filefun) {
  if (filesadded.indexOf("[" + filename + "]") == -1) {
    //  loadjscssfile(filename, filetype)
    filesadded += "[" + filename + "]" //List of files added in the form "[filename1],[filename2],etc"
    LoadScript(filename, filetype, filefun);

  } else { filefun() }

}



function LoadScript(filename, filetype, filefun) {
  var head = document.head || document.getElementsByTagName("head");


  // loading code borrowed directly from LABjs itself
  setTimeout(function () {
    if ("item" in head) { // check if ref is still a live node list
      if (!head[0]) { // append_to node not yet ready
        setTimeout(arguments.callee, 25);
        return;
      }
      head = head[0]; // reassign from live node list ref to pure node ref -- avoids nasty IE bug where changes to DOM invalidate live node lists
    }
    var scriptElem;
    if (filetype == "js") { //if filename is a external JavaScript file
      scriptElem = document.createElement('script');
      scriptElem.setAttribute("type", "text/javascript");
      scriptElem.src = filename;
    }
    else if (filetype == "css") { //if filename is an external CSS file
      scriptElem = document.createElement("link");
      scriptElem.setAttribute("rel", "stylesheet");
      scriptElem.setAttribute("type", "text/css");
      scriptElem.setAttribute("href", filename);
    }

    //        var scriptElem = document.createElement("script"),
    scriptdone = false;
    scriptElem.onload = scriptElem.onreadystatechange = function () {
      if ((scriptElem.readyState && scriptElem.readyState !== "complete" && scriptElem.readyState !== "loaded") || scriptdone) {
        return false;
      }
      scriptElem.onload = scriptElem.onreadystatechange = null;
      scriptdone = true;
      filefun();
      //            LABjsLoaded();
    };

    head.insertBefore(scriptElem, head.firstChild);
  }, 0);

};

function downloadURISafari(uri, name) {
  var link = document.createElement("a");
  link.download = name;
  link.href = uri;
  link.click();
  return true;
}

function downloadURI(uri, name) {
  if ((MD.isChrome) || (MD.isSafari))
    return downloadURISafari(uri, name);
  wldown = window.open(uri, "atabdown", "resizable,scrollbars");
}

