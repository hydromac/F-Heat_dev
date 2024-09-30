<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.34.10-Prizren" styleCategories="Symbology|Diagrams|Legend">
  <renderer-v2 forceraster="0" symbollevels="0" enableorderby="0" referencescale="-1" type="singleSymbol">
    <symbols>
      <symbol alpha="0.5" clip_to_extent="1" is_animated="0" force_rhr="0" frame_rate="10" name="0" type="fill">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" value="" type="QString"/>
            <Option name="properties"/>
            <Option name="type" value="collection" type="QString"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" class="SimpleFill" enabled="1" locked="0" id="{7918692b-2934-47b7-94c0-19d3faf11289}">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="color" value="164,164,164,255" type="QString"/>
            <Option name="joinstyle" value="bevel" type="QString"/>
            <Option name="offset" value="0,0" type="QString"/>
            <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="offset_unit" value="MM" type="QString"/>
            <Option name="outline_color" value="108,108,108,255" type="QString"/>
            <Option name="outline_style" value="solid" type="QString"/>
            <Option name="outline_width" value="0.26" type="QString"/>
            <Option name="outline_width_unit" value="MM" type="QString"/>
            <Option name="style" value="solid" type="QString"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties"/>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <selection mode="Default">
    <selectionColor invalid="1"/>
    <selectionSymbol>
      <symbol alpha="1" clip_to_extent="1" is_animated="0" force_rhr="0" frame_rate="10" name="" type="fill">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" value="" type="QString"/>
            <Option name="properties"/>
            <Option name="type" value="collection" type="QString"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" class="SimpleFill" enabled="1" locked="0" id="{cd662a03-f372-4ca1-8164-203be87cd695}">
          <Option type="Map">
            <Option name="border_width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="color" value="0,0,255,255" type="QString"/>
            <Option name="joinstyle" value="bevel" type="QString"/>
            <Option name="offset" value="0,0" type="QString"/>
            <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="offset_unit" value="MM" type="QString"/>
            <Option name="outline_color" value="35,35,35,255" type="QString"/>
            <Option name="outline_style" value="solid" type="QString"/>
            <Option name="outline_width" value="0.26" type="QString"/>
            <Option name="outline_width_unit" value="MM" type="QString"/>
            <Option name="style" value="solid" type="QString"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties"/>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </selectionSymbol>
  </selection>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <LinearlyInterpolatedDiagramRenderer attributeLegend="1" lowerValue="0" lowerHeight="0" diagramType="Pie" upperValue="200" upperHeight="25" lowerWidth="0" upperWidth="25" classificationField="Insgesamt_Energietraeger">
    <DiagramCategory minimumSize="2" lineSizeType="MM" scaleDependency="Diameter" spacingUnitScale="3x:0,0,0,0,0,0" penAlpha="255" barWidth="5" height="5" backgroundColor="#ffffff" enabled="1" labelPlacementMethod="XHeight" diagramOrientation="Up" width="5" penWidth="0.2" opacity="1" lineSizeScale="3x:0,0,0,0,0,0" backgroundAlpha="255" spacingUnit="MM" sizeScale="3x:0,0,0,0,0,0" spacing="5" rotationOffset="270" direction="0" sizeType="MM" scaleBasedVisibility="0" showAxis="1" maxScaleDenominator="1e+08" minScaleDenominator="0" penColor="#000000">
      <fontProperties italic="0" style="" underline="0" bold="0" strikethrough="0" description="MS Shell Dlg 2,3.3,-1,5,50,0,0,0,0,0"/>
      <attribute label="Erd- und Flüssiggas" color="#dada17" field="&quot;Gas&quot;" colorOpacity="1"/>
      <attribute label="Heizöl " color="#4f082c" field="&quot;Heizoel&quot;" colorOpacity="1"/>
      <attribute label="Holz / Holzpellets" color="#ab9b96" field="&quot;Holz_Holzpellets&quot;" colorOpacity="1"/>
      <attribute label="Biomasse / Biogas" color="#129165" field="&quot;Biomasse_Biogas&quot;" colorOpacity="1"/>
      <attribute label="Solar / Geothermie / Waermepumpen" color="#95fd78" field="&quot;Solar_Geothermie_Waermepumpen&quot;" colorOpacity="1"/>
      <attribute label="Strom" color="#8ac14b" field="&quot;Strom&quot;" colorOpacity="1"/>
      <attribute label="Kohle" color="#000000" field="&quot;Kohle&quot;" colorOpacity="1"/>
      <attribute label="Fern- / Nahwärme" color="#a2a8c1" field="&quot;Fernwaerme&quot;" colorOpacity="1"/>
      <attribute label="kein Energieträger" color="#eaeaea" field="&quot;kein_Energietraeger&quot;" colorOpacity="1"/>
      <axisSymbol>
        <symbol alpha="1" clip_to_extent="1" is_animated="0" force_rhr="0" frame_rate="10" name="" type="line">
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties"/>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
          <layer pass="0" class="SimpleLine" enabled="1" locked="0" id="{34cb24ed-b6f9-47a8-acd1-a206ad5495a7}">
            <Option type="Map">
              <Option name="align_dash_pattern" value="0" type="QString"/>
              <Option name="capstyle" value="square" type="QString"/>
              <Option name="customdash" value="5;2" type="QString"/>
              <Option name="customdash_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
              <Option name="customdash_unit" value="MM" type="QString"/>
              <Option name="dash_pattern_offset" value="0" type="QString"/>
              <Option name="dash_pattern_offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
              <Option name="dash_pattern_offset_unit" value="MM" type="QString"/>
              <Option name="draw_inside_polygon" value="0" type="QString"/>
              <Option name="joinstyle" value="bevel" type="QString"/>
              <Option name="line_color" value="35,35,35,255" type="QString"/>
              <Option name="line_style" value="solid" type="QString"/>
              <Option name="line_width" value="0.26" type="QString"/>
              <Option name="line_width_unit" value="MM" type="QString"/>
              <Option name="offset" value="0" type="QString"/>
              <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
              <Option name="offset_unit" value="MM" type="QString"/>
              <Option name="ring_filter" value="0" type="QString"/>
              <Option name="trim_distance_end" value="0" type="QString"/>
              <Option name="trim_distance_end_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
              <Option name="trim_distance_end_unit" value="MM" type="QString"/>
              <Option name="trim_distance_start" value="0" type="QString"/>
              <Option name="trim_distance_start_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
              <Option name="trim_distance_start_unit" value="MM" type="QString"/>
              <Option name="tweak_dash_pattern_on_corners" value="0" type="QString"/>
              <Option name="use_custom_dash" value="0" type="QString"/>
              <Option name="width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            </Option>
            <data_defined_properties>
              <Option type="Map">
                <Option name="name" value="" type="QString"/>
                <Option name="properties"/>
                <Option name="type" value="collection" type="QString"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
      </axisSymbol>
    </DiagramCategory>
    <data-defined-size-legend valign="bottom" title="Auswertung Zensus2022 Anteile der Energieträger" type="separated">
      <symbol alpha="1" clip_to_extent="1" is_animated="0" force_rhr="0" frame_rate="10" name="source" type="marker">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" value="" type="QString"/>
            <Option name="properties"/>
            <Option name="type" value="collection" type="QString"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" class="SimpleMarker" enabled="1" locked="0" id="{7e6197cb-c74d-4c7e-baa9-f10773c0eaad}">
          <Option type="Map">
            <Option name="angle" value="0" type="QString"/>
            <Option name="cap_style" value="square" type="QString"/>
            <Option name="color" value="255,0,0,255" type="QString"/>
            <Option name="horizontal_anchor_point" value="1" type="QString"/>
            <Option name="joinstyle" value="bevel" type="QString"/>
            <Option name="name" value="circle" type="QString"/>
            <Option name="offset" value="0,0" type="QString"/>
            <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="offset_unit" value="MM" type="QString"/>
            <Option name="outline_color" value="35,35,35,255" type="QString"/>
            <Option name="outline_style" value="solid" type="QString"/>
            <Option name="outline_width" value="0" type="QString"/>
            <Option name="outline_width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="outline_width_unit" value="MM" type="QString"/>
            <Option name="scale_method" value="diameter" type="QString"/>
            <Option name="size" value="1.2" type="QString"/>
            <Option name="size_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            <Option name="size_unit" value="MM" type="QString"/>
            <Option name="vertical_anchor_point" value="1" type="QString"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties"/>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <lineSymbol>
        <symbol alpha="1" clip_to_extent="1" is_animated="0" force_rhr="0" frame_rate="10" name="lineSymbol" type="line">
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties"/>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
          <layer pass="0" class="SimpleLine" enabled="1" locked="0" id="{0de2a8a8-4665-4214-ac0f-1f9ceb302a96}">
            <Option type="Map">
              <Option name="align_dash_pattern" value="0" type="QString"/>
              <Option name="capstyle" value="square" type="QString"/>
              <Option name="customdash" value="5;2" type="QString"/>
              <Option name="customdash_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
              <Option name="customdash_unit" value="MM" type="QString"/>
              <Option name="dash_pattern_offset" value="0" type="QString"/>
              <Option name="dash_pattern_offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
              <Option name="dash_pattern_offset_unit" value="MM" type="QString"/>
              <Option name="draw_inside_polygon" value="0" type="QString"/>
              <Option name="joinstyle" value="bevel" type="QString"/>
              <Option name="line_color" value="35,35,35,255" type="QString"/>
              <Option name="line_style" value="solid" type="QString"/>
              <Option name="line_width" value="0.26" type="QString"/>
              <Option name="line_width_unit" value="MM" type="QString"/>
              <Option name="offset" value="0" type="QString"/>
              <Option name="offset_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
              <Option name="offset_unit" value="MM" type="QString"/>
              <Option name="ring_filter" value="0" type="QString"/>
              <Option name="trim_distance_end" value="0" type="QString"/>
              <Option name="trim_distance_end_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
              <Option name="trim_distance_end_unit" value="MM" type="QString"/>
              <Option name="trim_distance_start" value="0" type="QString"/>
              <Option name="trim_distance_start_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
              <Option name="trim_distance_start_unit" value="MM" type="QString"/>
              <Option name="tweak_dash_pattern_on_corners" value="0" type="QString"/>
              <Option name="use_custom_dash" value="0" type="QString"/>
              <Option name="width_map_unit_scale" value="3x:0,0,0,0,0,0" type="QString"/>
            </Option>
            <data_defined_properties>
              <Option type="Map">
                <Option name="name" value="" type="QString"/>
                <Option name="properties"/>
                <Option name="type" value="collection" type="QString"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
      </lineSymbol>
      <text-style color="0,0,0,255" align="1">
        <font italic="0" size="8" weight="50" family="MS Shell Dlg 2"/>
      </text-style>
      <classes>
        <class label="25" size="25"/>
        <class label="50" size="50"/>
        <class label="100" size="100"/>
        <class label="200" size="200"/>
      </classes>
    </data-defined-size-legend>
  </LinearlyInterpolatedDiagramRenderer>
  <DiagramLayerSettings zIndex="0" obstacle="0" dist="0" showAll="1" priority="0" linePlacementFlags="18" placement="1">
    <properties>
      <Option type="Map">
        <Option name="name" value="" type="QString"/>
        <Option name="properties"/>
        <Option name="type" value="collection" type="QString"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <legend showLabelLegend="0" type="default-vector"/>
  <layerGeometryType>2</layerGeometryType>
</qgis>
