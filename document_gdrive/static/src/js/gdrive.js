openerp.document_gdrive = function(instance, m) {
    var _t = instance.web._t,
        QWeb = instance.web.qweb;

 // The Browser API key obtained from the Google Developers Console.
    var developerKey = 'xxxxxxxYYYYYYYY-12345678';

    // The Client ID obtained from the Google Developers Console. Replace with your own Client ID.
    var clientId = "1234567890-abcdefghijklmnopqrstuvwxyz.apps.googleusercontent.com"

    // Scope to use to access user's photos.
    var scope = ['https://www.googleapis.com/auth/photos'];

    var pickerApiLoaded = false;
    var oauthToken;

    // Use the API Loader script to load google.picker and gapi.auth.
    function onApiLoad() {
      gapi.load('auth', {'callback': onAuthApiLoad});
      gapi.load('picker', {'callback': onPickerApiLoad});
    }

    function onAuthApiLoad() {
      window.gapi.auth.authorize(
          {
            'client_id': clientId,
            'scope': scope,
            'immediate': false
          },
          handleAuthResult);
    }

    function onPickerApiLoad() {
      pickerApiLoaded = true;
      createPicker();
    }

    function handleAuthResult(authResult) {
      if (authResult && !authResult.error) {
        oauthToken = authResult.access_token;
        createPicker();
      }
    }

    // Create and render a Picker object for picking user Photos.
    function createPicker() {
      if (pickerApiLoaded && oauthToken) {
        var picker = new google.picker.PickerBuilder().
            addView(google.picker.ViewId.PHOTOS).
            setOAuthToken(oauthToken).
            setDeveloperKey(developerKey).
            setCallback(pickerCallback).
            build();
        picker.setVisible(true);
      }
    }

    // A simple callback implementation.
    function pickerCallback(data) {
      var url = 'nothing';
      if (data[google.picker.Response.ACTION] == google.picker.Action.PICKED) {
        var doc = data[google.picker.Response.DOCUMENTS][0];
        url = doc[google.picker.Document.URL];
      }
      var message = 'You picked: ' + url;
      document.getElementById('result').innerHTML = message;
    }
    
    instance.web.Sidebar.include({
        redraw: function() {
            var self = this;
            this._super.apply(this, arguments);
            self.$el.find('.oe_sidebar_add_attachment').after(QWeb.render('AddGDriveDocumentItem', {widget: self}))
            self.$el.find('.oe_sidebar_add_gdrive').on('click', function (e) {
                self.on_gdrive_doc();
            });
        },
        on_drive_doc: function() {
            
        	createPicker();
        	
        	/*var self = this;
            var view = self.getParent();
            var ids = ( view.fields_view.type != "form" )? view.groups.get_selection().ids : [ view.datarecord.id ];
            if( !_.isEmpty(ids) ){
                view.sidebar_eval_context().done(function (context) {
                    self.rpc("/web/action/load", { action_id: "document_gdrive.action_ir_attachment_add_gdrive" }).done(function(result) {
                        self.getParent().do_action(result, {
                            additional_context: {
                                'active_ids': ids,
                                'active_id': [ids[0]],
                                'active_model': view.dataset.model,
                            },
                        }); 
                    });
                });
            }*/
        },
    });

    instance.web.ActionManager = instance.web.ActionManager.extend({
        ir_actions_act_close_wizard_and_reload_view: function (action, options) {
            if (!this.dialog) {
                options.on_close();
            }
            this.dialog_stop();
            this.inner_widget.views[this.inner_widget.active_view].controller.reload();
            return $.when();
        },
    });

};
