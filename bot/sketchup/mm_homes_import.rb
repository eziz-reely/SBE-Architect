# encoding: UTF-8
# MM Homes · SketchUp paplašinājums: importē redaktora eksportētos MM modeļus (.zip vai .rb)
require 'sketchup.rb'
require 'extensions.rb'

module MMHomes
  module Import
    unless file_loaded?(__FILE__)
      ext = SketchupExtension.new('MM Homes modeļu imports', 'mm_homes_import/main')
      ext.description = 'Importē MM Homes redaktora 3D modeļus: Extensions → MM Homes → Importēt MM modeli.'
      ext.version = '1.0.0'
      ext.creator = 'MM Homes'
      ext.copyright = 'MM Homes'
      Sketchup.register_extension(ext, true)
      file_loaded(__FILE__)
    end
  end
end
