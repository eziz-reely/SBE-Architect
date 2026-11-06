# encoding: UTF-8
require 'sketchup.rb'
require 'zlib'

module MMHomes
  module Import
    # .rb modelis no zip faila (redaktora eksports: bez saspiešanas; der arī parasts deflate zip)
    def self.rb_from_zip(path)
      data = File.binread(path)
      i = 0
      sig = "PK\x03\x04".b
      while (i = data.index(sig, i))
        method = data[i + 8, 2].unpack1('v')
        csize = data[i + 18, 4].unpack1('V')
        nlen, xlen = data[i + 26, 4].unpack('vv')
        name = data[i + 30, nlen].dup.force_encoding('UTF-8')
        start = i + 30 + nlen + xlen
        body = data[start, csize]
        if name.downcase.end_with?('.rb')
          body = Zlib::Inflate.new(-Zlib::MAX_WBITS).inflate(body) if method == 8
          return body.force_encoding('UTF-8')
        end
        i = start + csize
      end
      nil
    end

    def self.import
      path = UI.openpanel('Izvēlies MM modeli (.zip vai .rb)', '', 'MM modelis|*.zip;*.rb||')
      return unless path
      src = path.downcase.end_with?('.zip') ? rb_from_zip(path) : File.read(path, encoding: 'UTF-8')
      unless src && src.include?('Sketchup.active_model')
        UI.messagebox('Šajā failā nav MM modeļa. Eksportē no redaktora: Eksportēt → SketchUp.')
        return
      end
      old = $VERBOSE
      $VERBOSE = nil   # modeļa materiālu konstantes var pārdefinēt bez brīdinājumiem
      begin
        TOPLEVEL_BINDING.eval(src, path)
      ensure
        $VERBOSE = old
      end
    rescue StandardError => e
      Sketchup.active_model.abort_operation rescue nil
      UI.messagebox("MM modeļa imports neizdevās:\n#{e.message}")
    end

    unless file_loaded?(__FILE__)
      menu = UI.menu('Extensions').add_submenu('MM Homes')
      menu.add_item('Importēt MM modeli…') { import }
      cmd = UI::Command.new('Importēt MM modeli') { import }
      cmd.tooltip = 'Importēt MM modeli'
      cmd.status_bar_text = 'Importē MM Homes redaktora eksportu (.zip vai .rb)'
      UI.menu('File').add_item(cmd)
      file_loaded(__FILE__)
    end
  end
end
