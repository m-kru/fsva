library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library vhdl_simple;

entity gbt_link_checker is
  port (
    clk   : in std_logic;

    system_tx_data_i : in  std_logic_vector(83 downto 0);
    system_rx_data_o : out std_logic_vector(83 downto 0);
    system_tx_extra_data_widebus_i : in  std_logic_vector(31 downto 0) := (others => 'X');
    system_rx_extra_data_widebus_o : out std_logic_vector(31 downto 0);

    gbt_tx_frame_o : out std_logic_vector(83 downto 0);
    gbt_rx_frame_i : in  std_logic_vector(83 downto 0);
    gbt_tx_frame_extra_data_widebus_o : out std_logic_vector(31 downto 0);
    gbt_rx_frame_extra_data_widebus_i : in  std_logic_vector(31 downto 0) := (others => 'X');

    enable_i            : in  std_logic;
    initial_value_i     : in  std_logic_vector(19 downto 0);
    widebus_mode_i      : in  std_logic;
    synced_o            : out std_logic;
    num_of_err_frames_o : out std_logic_vector(31 downto 0)
  );
end gbt_link_checker;

architecture structural of gbt_link_checker is

  signal s_tx_data_o               : std_logic_vector(83 downto 0);
  signal s_tx_extra_data_widebus_o : std_logic_vector(31 downto 0);

begin

  gbt_pattern_generator_0 : entity work.gbt_pattern_generator
  port map (
    clk                     => clk,
    rst_n                   => enable_i,
    initial_value_i         => initial_value_i,
    tx_data_o               => s_tx_data_o,
    tx_extra_data_widebus_o => s_tx_extra_data_widebus_o
  );

  tx_mux_2x1_0 : entity vhdl_simple.mux_2x1
  generic map (
    G_WIDTH  => 84
  )
  port map (
    addr_i => enable_i,
    in_0_i => system_tx_data_i,
    in_1_i => s_tx_data_o,
    out_o  => gbt_tx_frame_o
  );

  tx_mux_2x1_1 : entity vhdl_simple.mux_2x1
  generic map (
    G_WIDTH  => 32
  )
  port map (
    addr_i => enable_i,
    in_0_i => system_tx_extra_data_widebus_i,
    in_1_i => s_tx_extra_data_widebus_o,
    out_o  => gbt_tx_frame_extra_data_widebus_o
  );

  rx_mux_2x1_0 : entity vhdl_simple.mux_2x1
  generic map (
    G_WIDTH  => 84
  )
  port map (
    addr_i => enable_i,
    in_0_i => gbt_rx_frame_i,
    in_1_i => (others => '0'),
    out_o  => system_rx_data_o
  );

  rx_mux_2x1_1 : entity vhdl_simple.mux_2x1
  generic map (
    G_WIDTH  => 32
  )
  port map (
    addr_i => enable_i,
    in_0_i => gbt_rx_frame_extra_data_widebus_i,
    in_1_i => (others => '0'),
    out_o  => system_rx_extra_data_widebus_o
  );

  gbt_pattern_checker_0 : entity work.gbt_pattern_checker
  generic map (
    NUM_FRAMES_TO_SYNC  => 3
  )
  port map (
    clk                     => clk,
    rst_n                   => enable_i,
    widebus_mode_i          => widebus_mode_i,
    rx_data_i               => gbt_rx_frame_i,
    rx_extra_data_widebus_i => gbt_rx_frame_extra_data_widebus_i,
    synced_o                => synced_o,
    num_of_err_frames_o     => num_of_err_frames_o
  );

end structural;
